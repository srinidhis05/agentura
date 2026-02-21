/**
 * Risk Manager
 * ============
 *
 * Pure business logic for risk management.
 * Hard-coded limits that CANNOT be bypassed.
 *
 * Ported from: FinceptTerminal/voltagent/src/core/risk/risk-manager.ts
 * Enhanced with: Cross-border currency limits, circuit breakers
 */

import type {
  Signal,
  Portfolio,
  RiskCheck,
  RiskLimits,
  RiskViolation,
  CircuitBreakerStatus,
  Currency,
} from '../domain/types.js';
import type { RiskPort } from '../domain/interfaces.js';

// HARD-CODED LIMITS - These are non-negotiable and FROZEN
const LIMITS: RiskLimits = {
  // Position Sizing
  maxPositionPct: { value: 2.0 },          // Max 2% per position
  maxSectorPct: { value: 25.0 },           // Max 25% in any sector
  maxConcentration: 5,                      // Max 5 positions per sector

  // Loss Prevention
  maxDailyLossPct: { value: 5.0 },         // Stop trading if down 5%
  maxWeeklyLossPct: { value: 10.0 },       // Weekly circuit breaker
  maxDrawdownPct: { value: 15.0 },         // Alert threshold

  // Trading Frequency
  maxTradesPerDay: 10,                      // Prevent overtrading
  minHoldingPeriodSec: 60,                  // Min 60 seconds (anti-churn)

  // Trade Quality
  requireStopLoss: true,                    // Every trade needs SL
  minRiskRewardRatio: 1.5,                  // Don't take bad R:R trades
  minScoreThreshold: 5.5,                   // Only trade scores > 5.5

  // Human Oversight - Cross-border aware
  humanApprovalThreshold: {
    INR: 50000,    // ₹50K
    USD: 500,      // $500
    AED: 2000,     // 2000 AED
    GBP: 400,      // £400
    EUR: 450,      // €450
    SGD: 700,      // S$700
    CAD: 700,      // C$700
    AUD: 800,      // A$800
  } as Record<Currency, number>,
};

// Circuit breaker state
let circuitBreaker: CircuitBreakerStatus = {
  isHalted: false,
  reason: null,
  haltedAt: null,
  resumesAt: null,
};

/**
 * Create risk manager with hard-coded limits.
 */
export function createRiskManager(): RiskPort {
  return {
    getLimits(): RiskLimits {
      // Return frozen copy - cannot be modified
      return Object.freeze({ ...LIMITS });
    },

    validateSignal(
      signal: Signal,
      portfolio: Portfolio,
      dailyStats: { trades: number; pnl: number }
    ): RiskCheck {
      const violations: RiskViolation[] = [];
      const warnings: string[] = [];

      // Check circuit breaker first
      if (circuitBreaker.isHalted) {
        violations.push({
          rule: 'CIRCUIT_BREAKER',
          severity: 'halt',
          limit: 'Trading halted',
          actual: circuitBreaker.reason || 'Unknown',
          message: `Trading halted: ${circuitBreaker.reason}`,
        });
        return { approved: false, violations, warnings };
      }

      const portfolioValue = portfolio.totalValue.amount;
      const positionValue = signal.entryPrice * signal.quantity;
      const positionPct = (positionValue / portfolioValue) * 100;

      // Rule 1: Max position size (2%)
      if (positionPct > LIMITS.maxPositionPct.value) {
        const maxQuantity = Math.floor(
          (portfolioValue * LIMITS.maxPositionPct.value / 100) / signal.entryPrice
        );
        violations.push({
          rule: 'MAX_POSITION',
          severity: 'block',
          limit: `${LIMITS.maxPositionPct.value}%`,
          actual: `${positionPct.toFixed(1)}%`,
          message: `Position ${positionPct.toFixed(1)}% exceeds max ${LIMITS.maxPositionPct.value}%. Max quantity: ${maxQuantity}`,
        });
      }

      // Rule 2: Daily trades limit
      if (dailyStats.trades >= LIMITS.maxTradesPerDay) {
        violations.push({
          rule: 'MAX_DAILY_TRADES',
          severity: 'block',
          limit: `${LIMITS.maxTradesPerDay}`,
          actual: `${dailyStats.trades}`,
          message: `Daily trade limit reached (${dailyStats.trades}/${LIMITS.maxTradesPerDay})`,
        });
      } else if (dailyStats.trades >= LIMITS.maxTradesPerDay - 2) {
        warnings.push(`Approaching trade limit (${dailyStats.trades}/${LIMITS.maxTradesPerDay})`);
      }

      // Rule 3: Daily loss circuit breaker (5%)
      const dailyLossPct = Math.abs(Math.min(0, dailyStats.pnl)) / portfolioValue * 100;
      if (dailyLossPct >= LIMITS.maxDailyLossPct.value) {
        violations.push({
          rule: 'MAX_DAILY_LOSS',
          severity: 'halt',
          limit: `${LIMITS.maxDailyLossPct.value}%`,
          actual: `${dailyLossPct.toFixed(1)}%`,
          message: `Daily loss limit reached (${dailyLossPct.toFixed(1)}%). Trading halted.`,
        });
        // Trigger circuit breaker
        this.triggerCircuitBreaker('Daily loss limit exceeded', 24 * 60 * 60 * 1000);
      } else if (dailyLossPct >= LIMITS.maxDailyLossPct.value * 0.6) {
        warnings.push(`Daily loss at ${dailyLossPct.toFixed(1)}% (limit: ${LIMITS.maxDailyLossPct.value}%)`);
      }

      // Rule 4: Stop loss required
      if (LIMITS.requireStopLoss && !signal.stopLoss) {
        violations.push({
          rule: 'STOP_LOSS_REQUIRED',
          severity: 'block',
          limit: 'Required',
          actual: 'Missing',
          message: 'Stop loss is required for all trades',
        });
      }

      // Rule 5: Minimum score threshold
      if (signal.score < LIMITS.minScoreThreshold) {
        violations.push({
          rule: 'MIN_SCORE',
          severity: 'block',
          limit: `${LIMITS.minScoreThreshold}`,
          actual: `${signal.score.toFixed(1)}`,
          message: `Score ${signal.score.toFixed(1)} below minimum ${LIMITS.minScoreThreshold}`,
        });
      }

      // Rule 6: Risk/Reward ratio
      if (signal.stopLoss && signal.target) {
        const risk = Math.abs(signal.entryPrice - signal.stopLoss);
        const reward = Math.abs(signal.target - signal.entryPrice);
        const rr = risk > 0 ? reward / risk : 0;

        if (rr < LIMITS.minRiskRewardRatio) {
          violations.push({
            rule: 'MIN_RISK_REWARD',
            severity: 'block',
            limit: `${LIMITS.minRiskRewardRatio}:1`,
            actual: `${rr.toFixed(2)}:1`,
            message: `Risk/Reward ${rr.toFixed(2)}:1 below minimum ${LIMITS.minRiskRewardRatio}:1`,
          });
        }
      }

      // Rule 7: Sector concentration
      const symbol = signal.symbol;
      const sectorExposure = portfolio.sectorExposure;
      // Note: Would need to look up sector for symbol in real implementation

      // Calculate adjusted quantity if position too large
      let adjustedQuantity: number | undefined;
      if (positionPct > LIMITS.maxPositionPct.value) {
        adjustedQuantity = Math.floor(
          (portfolioValue * LIMITS.maxPositionPct.value / 100) / signal.entryPrice
        );
      }

      return {
        approved: violations.length === 0,
        violations,
        warnings,
        adjustedQuantity,
      };
    },

    calculatePositionSize(
      price: number,
      portfolioValue: number,
      winRate: number = 0.5,
      avgWin: number = 0.08,
      avgLoss: number = 0.04,
      volatility: number = 0.2
    ): number {
      // Kelly Criterion: f* = (p*b - q) / b
      // where p = win rate, q = 1-p, b = avg win / avg loss
      const p = winRate;
      const q = 1 - p;
      const b = avgWin / avgLoss;

      const kellyPct = (p * b - q) / b;

      // Half-Kelly for safety
      const halfKelly = Math.max(0, kellyPct / 2);

      // Volatility adjustment - reduce size in high volatility
      const volAdjusted = halfKelly * (1 / (1 + volatility));

      // Cap at max position limit
      const cappedPct = Math.min(volAdjusted, LIMITS.maxPositionPct.value / 100);

      // Calculate quantity
      const positionValue = portfolioValue * cappedPct;
      return Math.floor(positionValue / price);
    },

    getCircuitBreakerStatus(): CircuitBreakerStatus {
      // Auto-reset if time has passed
      if (circuitBreaker.isHalted && circuitBreaker.resumesAt) {
        if (new Date() >= circuitBreaker.resumesAt) {
          this.resetCircuitBreaker();
        }
      }
      return { ...circuitBreaker };
    },

    triggerCircuitBreaker(reason: string, durationMs: number): void {
      const now = new Date();
      circuitBreaker = {
        isHalted: true,
        reason,
        haltedAt: now,
        resumesAt: new Date(now.getTime() + durationMs),
      };
    },

    resetCircuitBreaker(): void {
      circuitBreaker = {
        isHalted: false,
        reason: null,
        haltedAt: null,
        resumesAt: null,
      };
    },
  };
}

/**
 * Check if a trade requires human approval based on amount.
 */
export function requiresHumanApproval(
  amount: number,
  currency: Currency
): boolean {
  const threshold = LIMITS.humanApprovalThreshold[currency] || 500;
  return amount > threshold;
}

/**
 * Get risk status summary for dashboard.
 */
export function getRiskStatus(
  portfolio: Portfolio,
  dailyStats: { trades: number; pnl: number }
): {
  dailyLossPct: number;
  dailyLossLimit: number;
  tradesUsed: number;
  tradesLimit: number;
  isHealthy: boolean;
  circuitBreaker: CircuitBreakerStatus;
} {
  const portfolioValue = portfolio.totalValue.amount;
  const dailyLossPct = Math.abs(Math.min(0, dailyStats.pnl)) / portfolioValue * 100;

  return {
    dailyLossPct,
    dailyLossLimit: LIMITS.maxDailyLossPct.value,
    tradesUsed: dailyStats.trades,
    tradesLimit: LIMITS.maxTradesPerDay,
    isHealthy: dailyLossPct < LIMITS.maxDailyLossPct.value * 0.6 &&
               dailyStats.trades < LIMITS.maxTradesPerDay - 2,
    circuitBreaker,
  };
}
