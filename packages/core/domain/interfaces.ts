/**
 * Core Domain Interfaces (Ports)
 * ==============================
 *
 * Abstractions that define what the domain needs.
 * Implementations live in infra/. This is dependency inversion.
 */

import type {
  Price,
  Fundamentals,
  Technicals,
  StockScore,
  Signal,
  RiskCheck,
  RiskLimits,
  Portfolio,
  Order,
  Goal,
  FxRate,
  CurrencyImpact,
  GeopoliticalScenario,
  TradeOutcome,
  LearnedPattern,
  Exchange,
  RiskProfile,
  Market,
  Currency,
  CircuitBreakerStatus,
} from './types.js';

// ============================================================================
// MARKET DATA PORT
// ============================================================================

export interface MarketDataPort {
  getPrice(symbol: string, exchange: Exchange): Promise<Price | null>;
  getPrices(symbols: readonly string[]): Promise<Map<string, Price>>;
  getFundamentals(symbol: string): Promise<Fundamentals | null>;
  getTechnicals(symbol: string, period?: string): Promise<Technicals | null>;
}

// ============================================================================
// SCORER PORT
// ============================================================================

export interface ScorerPort {
  score(
    symbol: string,
    fundamentals: Fundamentals,
    technicals: Technicals,
    riskProfile: RiskProfile
  ): StockScore;

  scoreAndRank(
    data: ReadonlyArray<{ symbol: string; fundamentals: Fundamentals; technicals: Technicals }>,
    riskProfile: RiskProfile
  ): readonly StockScore[];
}

// ============================================================================
// RISK PORT
// ============================================================================

export interface RiskPort {
  getLimits(): RiskLimits;

  validateSignal(
    signal: Signal,
    portfolio: Portfolio,
    dailyStats: { trades: number; pnl: number }
  ): RiskCheck;

  calculatePositionSize(
    price: number,
    portfolioValue: number,
    winRate?: number,
    avgWin?: number,
    avgLoss?: number,
    volatility?: number
  ): number;

  getCircuitBreakerStatus(): CircuitBreakerStatus;

  triggerCircuitBreaker(reason: string, durationMs: number): void;

  resetCircuitBreaker(): void;
}

// ============================================================================
// BROKER PORT
// ============================================================================

export interface BrokerPort {
  readonly name: string;

  isConnected(): Promise<boolean>;

  buy(
    symbol: string,
    exchange: Exchange,
    quantity: number,
    orderType?: 'MARKET' | 'LIMIT',
    price?: number
  ): Promise<Order>;

  sell(
    symbol: string,
    exchange: Exchange,
    quantity: number,
    orderType?: 'MARKET' | 'LIMIT',
    price?: number
  ): Promise<Order>;

  setStopLoss(
    symbol: string,
    exchange: Exchange,
    quantity: number,
    triggerPrice: number
  ): Promise<Order>;

  getPortfolio(): Promise<Portfolio>;

  getOrders(): Promise<readonly Order[]>;
}

// ============================================================================
// CROSS-BORDER PORT
// ============================================================================

export interface CrossBorderPort {
  getFxRate(from: Currency, to: Currency): Promise<FxRate>;

  getFxRates(baseCurrency: Currency): Promise<Map<Currency, FxRate>>;

  calculateCurrencyImpact(
    symbol: string,
    baseCurrency: Currency,
    period: '1M' | '3M' | '6M' | '1Y' | '3Y'
  ): Promise<CurrencyImpact>;

  getOptimalRemittanceTime(
    from: Currency,
    to: Currency,
    amount: number
  ): Promise<{ recommendation: string; expectedRate: number; confidence: number }>;
}

// ============================================================================
// GOALS PORT
// ============================================================================

export interface GoalsPort {
  createGoal(goal: Omit<Goal, 'id' | 'currentAmount'>): Promise<Goal>;

  getGoal(goalId: string): Promise<Goal | null>;

  getAllGoals(userId: string): Promise<readonly Goal[]>;

  updateGoalProgress(goalId: string, amount: number): Promise<Goal>;

  suggestAllocation(
    targetAmount: number,
    targetDate: Date,
    riskProfile: RiskProfile,
    baseCurrency: Currency
  ): Promise<Goal['allocations']>;

  rebalanceGoal(goalId: string): Promise<readonly Signal[]>;
}

// ============================================================================
// GEOPOLITICS PORT
// ============================================================================

export interface GeopoliticsPort {
  getScenarios(): readonly GeopoliticalScenario[];

  detectScenario(input: string): GeopoliticalScenario | null;

  getStocksForScenario(scenarioId: string, markets: readonly Market[]): readonly string[];

  getCurrencyImpact(scenarioId: string): Record<Currency, number>;
}

// ============================================================================
// LEARNING PORT
// ============================================================================

export interface LearningPort {
  recordTrade(outcome: TradeOutcome): Promise<void>;

  getPattern(type: string, value: string): Promise<LearnedPattern | null>;

  getAllPatterns(): Promise<readonly LearnedPattern[]>;

  recordFeedback(
    tradeId: string,
    feedbackType: string,
    details: string,
    suggestion?: string
  ): Promise<void>;

  getRecentOutcomes(hours: number): Promise<{
    total: number;
    wins: number;
    losses: number;
    winRate: number;
  }>;

  getPerformanceByGoal(goalId: string): Promise<{
    totalTrades: number;
    winRate: number;
    totalPnl: number;
    sharpeRatio: number;
  }>;
}

// ============================================================================
// NOTIFIER PORT
// ============================================================================

export interface NotifierPort {
  notify(message: string, channel?: 'push' | 'email' | 'slack'): Promise<boolean>;

  requestApproval(
    message: string,
    timeout: number,
    tradeDetails?: Signal
  ): Promise<boolean | null>;
}

// ============================================================================
// MEMORY PORT
// ============================================================================

export interface MemoryPort {
  set<T>(key: string, value: T): Promise<void>;
  get<T>(key: string): Promise<T | null>;
  delete(key: string): Promise<void>;
  list(prefix: string): Promise<readonly string[]>;
}

// ============================================================================
// LOGGER PORT
// ============================================================================

export interface LoggerPort {
  debug(message: string, context?: Record<string, unknown>): void;
  info(message: string, context?: Record<string, unknown>): void;
  warn(message: string, context?: Record<string, unknown>): void;
  error(message: string, context?: Record<string, unknown>): void;
}
