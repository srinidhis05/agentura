/**
 * Core Domain Types
 * =================
 *
 * Pure TypeScript types with ZERO external dependencies.
 * Represents business domain: trading, goals, risk, cross-border.
 */

// ============================================================================
// VALUE OBJECTS (Immutable)
// ============================================================================

export type Currency = 'INR' | 'USD' | 'AED' | 'GBP' | 'EUR' | 'SGD' | 'CAD' | 'AUD';
export type Exchange = 'NSE' | 'BSE' | 'NASDAQ' | 'NYSE' | 'LSE' | 'CRYPTO';
export type Action = 'BUY' | 'SELL' | 'HOLD';
export type Recommendation = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';
export type RiskProfile = 'conservative' | 'moderate' | 'aggressive';
export type TradingMode = 'paper' | 'live';
export type Market = 'india' | 'us' | 'uk' | 'uae' | 'singapore' | 'crypto';

export interface Money {
  readonly amount: number;
  readonly currency: Currency;
}

export interface Percentage {
  readonly value: number; // 0-100
}

// ============================================================================
// MARKET DATA
// ============================================================================

export interface Price {
  readonly symbol: string;
  readonly exchange: Exchange;
  readonly current: number;
  readonly open: number;
  readonly high: number;
  readonly low: number;
  readonly volume: number;
  readonly change: Percentage;
  readonly currency: Currency;
  readonly timestamp: Date;
}

export interface Fundamentals {
  readonly symbol: string;
  readonly peRatio: number | null;
  readonly pbRatio: number | null;
  readonly dividendYield: Percentage | null;
  readonly roe: Percentage | null;
  readonly profitMargin: Percentage | null;
  readonly debtToEquity: number | null;
  readonly beta: number | null;
  readonly marketCap: Money | null;
  readonly sector: string | null;
  readonly industry: string | null;
}

export interface Technicals {
  readonly symbol: string;
  readonly rsi: number;
  readonly rsiSignal: 'OVERSOLD' | 'OVERBOUGHT' | 'NEUTRAL';
  readonly macd: number;
  readonly macdSignal: number;
  readonly macdHistogram: number;
  readonly macdTrend: 'BULLISH' | 'BEARISH';
  readonly sma20: number;
  readonly sma50: number | null;
  readonly sma200: number | null;
  readonly trend: 'STRONG_UPTREND' | 'UPTREND' | 'MIXED' | 'DOWNTREND' | 'STRONG_DOWNTREND';
  readonly bbUpper: number;
  readonly bbLower: number;
  readonly bbPercentB: number;
}

// ============================================================================
// SCORING
// ============================================================================

export interface FactorScores {
  readonly value: number;      // 0-30
  readonly quality: number;    // 0-30
  readonly momentum: number;   // 0-20
  readonly technical: number;  // 0-30
  readonly risk: number;       // 0-15
}

export interface StockScore {
  readonly symbol: string;
  readonly exchange: Exchange;
  readonly score: number;      // 0-10
  readonly recommendation: Recommendation;
  readonly factorScores: FactorScores;
  readonly bullSignals: readonly string[];
  readonly bearSignals: readonly string[];
  readonly timestamp: Date;
}

// ============================================================================
// SIGNALS & TRADES
// ============================================================================

export interface Signal {
  readonly id: string;
  readonly timestamp: Date;
  readonly action: Action;
  readonly symbol: string;
  readonly exchange: Exchange;
  readonly quantity: number;
  readonly entryPrice: number;
  readonly stopLoss: number;
  readonly target: number;
  readonly confidence: Percentage;
  readonly score: number;
  readonly reasons: readonly string[];
  readonly metadata?: SignalMetadata;
}

export interface SignalMetadata {
  readonly scenario?: string;
  readonly goalId?: string;
  readonly rebalanceReason?: string;
}

// ============================================================================
// RISK MANAGEMENT
// ============================================================================

export interface RiskLimits {
  // Position Sizing
  readonly maxPositionPct: Percentage;    // Max single position size
  readonly maxSectorPct: Percentage;      // Max sector concentration
  readonly maxConcentration: number;      // Max positions per sector

  // Loss Prevention
  readonly maxDailyLossPct: Percentage;   // Stop trading threshold
  readonly maxWeeklyLossPct: Percentage;  // Weekly circuit breaker
  readonly maxDrawdownPct: Percentage;    // Alert threshold

  // Trading Frequency
  readonly maxTradesPerDay: number;       // Overtrading prevention
  readonly minHoldingPeriodSec: number;   // Anti-churn

  // Trade Quality
  readonly requireStopLoss: boolean;      // Every trade needs SL
  readonly minRiskRewardRatio: number;    // Min R:R ratio
  readonly minScoreThreshold: number;     // Min score to trade

  // Human Oversight
  readonly humanApprovalThreshold: Record<Currency, number>;
}

export interface RiskCheck {
  readonly approved: boolean;
  readonly violations: readonly RiskViolation[];
  readonly warnings: readonly string[];
  readonly adjustedQuantity?: number;     // Suggested safe quantity
}

export interface RiskViolation {
  readonly rule: string;
  readonly severity: 'warning' | 'block' | 'halt';
  readonly limit: string;
  readonly actual: string;
  readonly message: string;
}

export interface CircuitBreakerStatus {
  readonly isHalted: boolean;
  readonly reason: string | null;
  readonly haltedAt: Date | null;
  readonly resumesAt: Date | null;
}

// ============================================================================
// PORTFOLIO
// ============================================================================

export interface Position {
  readonly symbol: string;
  readonly exchange: Exchange;
  readonly quantity: number;
  readonly avgPrice: number;
  readonly currentPrice: number;
  readonly pnl: Money;
  readonly pnlPct: Percentage;
  readonly stopLoss?: number;
  readonly currency: Currency;
}

export interface Portfolio {
  readonly cash: Money;
  readonly positions: readonly Position[];
  readonly totalValue: Money;
  readonly dailyPnl: Money;
  readonly dailyPnlPct: Percentage;
  readonly sectorExposure: Record<string, Percentage>;
  readonly currencyExposure: Record<Currency, Percentage>;
}

// ============================================================================
// GOALS (Cross-Border Specific)
// ============================================================================

export interface Goal {
  readonly id: string;
  readonly name: string;
  readonly targetAmount: Money;
  readonly currentAmount: Money;
  readonly targetDate: Date;
  readonly riskProfile: RiskProfile;
  readonly priority: 'critical' | 'important' | 'flexible';
  readonly allocations: readonly GoalAllocation[];
}

export interface GoalAllocation {
  readonly assetClass: 'equity' | 'debt' | 'gold' | 'crypto' | 'cash';
  readonly market: Market;
  readonly targetPct: Percentage;
  readonly currentPct: Percentage;
  readonly currency: Currency;
}

// ============================================================================
// CROSS-BORDER
// ============================================================================

export interface FxRate {
  readonly from: Currency;
  readonly to: Currency;
  readonly rate: number;
  readonly timestamp: Date;
}

export interface CurrencyImpact {
  readonly nominalReturn: Percentage;
  readonly fxImpact: Percentage;
  readonly realReturn: Percentage;   // nominalReturn - fxImpact
  readonly period: '1M' | '3M' | '6M' | '1Y' | '3Y';
}

// ============================================================================
// GEOPOLITICS
// ============================================================================

export interface GeopoliticalScenario {
  readonly id: string;
  readonly name: string;
  readonly framework: string;
  readonly triggerWords: readonly string[];
  readonly bullishSectors: readonly string[];
  readonly bearishSectors: readonly string[];
  readonly stocks: Record<Market, readonly string[]>;
  readonly currencyImpact: Record<Currency, number>;  // -1 to +1
}

// ============================================================================
// EXECUTION
// ============================================================================

export interface Order {
  readonly id: string;
  readonly timestamp: Date;
  readonly action: Action;
  readonly symbol: string;
  readonly exchange: Exchange;
  readonly quantity: number;
  readonly price: number;
  readonly status: 'PENDING' | 'FILLED' | 'REJECTED' | 'CANCELLED';
  readonly broker: 'paper' | 'zerodha' | 'groww' | 'alpaca' | 'ibkr';
  readonly currency: Currency;
}

// ============================================================================
// LEARNING
// ============================================================================

export interface TradeOutcome {
  readonly tradeId: string;
  readonly symbol: string;
  readonly action: Action;
  readonly entryPrice: number;
  readonly exitPrice: number;
  readonly quantity: number;
  readonly pnl: number;
  readonly pnlPct: number;
  readonly outcome: 'profit' | 'loss' | 'stopped_out' | 'target_hit';
  readonly holdDays: number;
  readonly recommendation: Recommendation;
  readonly score: number;
  readonly reasons: readonly string[];
  readonly goalId?: string;
}

export interface LearnedPattern {
  readonly patternType: 'recommendation' | 'reason' | 'scenario' | 'sector';
  readonly patternValue: string;
  readonly totalTrades: number;
  readonly wins: number;
  readonly losses: number;
  readonly avgPnlPct: number;
  readonly winRate: number;
}
