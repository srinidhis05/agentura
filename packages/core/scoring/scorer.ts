/**
 * Multi-Factor Scorer
 * ===================
 *
 * Pure business logic - ZERO external dependencies.
 * Implements scoring algorithm for stock recommendations.
 *
 * Ported from: FinceptTerminal/voltagent/src/core/scoring/scorer.ts
 */

import type {
  Fundamentals,
  Technicals,
  StockScore,
  FactorScores,
  Recommendation,
  RiskProfile,
  Exchange,
} from '../domain/types.js';
import type { ScorerPort } from '../domain/interfaces.js';

// Factor weights by risk profile
const WEIGHTS: Record<RiskProfile, Record<keyof FactorScores, number>> = {
  conservative: { value: 0.25, quality: 0.30, momentum: 0.15, technical: 0.15, risk: 0.15 },
  moderate: { value: 0.20, quality: 0.25, momentum: 0.25, technical: 0.20, risk: 0.10 },
  aggressive: { value: 0.15, quality: 0.20, momentum: 0.30, technical: 0.25, risk: 0.10 },
};

// Score thresholds
const THRESHOLDS = {
  STRONG_BUY: 6.5,
  BUY: 5.5,
  HOLD: 4.5,
} as const;

/**
 * Calculate value score (0-30).
 * Low P/E, Low P/B, High Dividend = good value.
 */
function calculateValueScore(f: Fundamentals): number {
  let score = 0;

  // P/E (0-10)
  const pe = f.peRatio ?? 0;
  if (pe > 0 && pe < 15) score += 10;
  else if (pe > 0 && pe < 25) score += 5;

  // P/B (0-10)
  const pb = f.pbRatio ?? 0;
  if (pb > 0 && pb < 2) score += 10;
  else if (pb > 0 && pb < 4) score += 5;

  // Dividend (0-10)
  const div = f.dividendYield?.value ?? 0;
  if (div > 3) score += 10;
  else if (div > 1) score += 5;

  return score;
}

/**
 * Calculate quality score (0-30).
 * High ROE, High Margins, Low Debt = good quality.
 */
function calculateQualityScore(f: Fundamentals): number {
  let score = 0;

  // ROE (0-10)
  const roe = f.roe?.value ?? 0;
  if (roe > 15) score += 10;
  else if (roe > 10) score += 5;

  // Margin (0-10)
  const margin = f.profitMargin?.value ?? 0;
  if (margin > 10) score += 10;
  else if (margin > 5) score += 5;

  // D/E (0-10)
  const de = f.debtToEquity ?? 0;
  if (de >= 0 && de < 1) score += 10;
  else if (de >= 0 && de < 2) score += 5;

  return score;
}

/**
 * Calculate momentum score (0-20).
 * Based on RSI and trend.
 */
function calculateMomentumScore(t: Technicals): number {
  let score = 0;

  // RSI position (0-10)
  if (t.rsi > 30 && t.rsi < 70) score += 10;
  else score += 5;

  // Trend (0-10)
  if (t.trend === 'STRONG_UPTREND' || t.trend === 'UPTREND') score += 10;
  else if (t.trend === 'MIXED') score += 5;

  return score;
}

/**
 * Calculate technical score (0-30).
 * RSI signal, MACD trend, price vs SMA.
 */
function calculateTechnicalScore(t: Technicals, price: number): number {
  let score = 0;

  // RSI signal (0-10)
  if (t.rsiSignal === 'OVERSOLD') score += 10;
  else if (t.rsiSignal === 'NEUTRAL') score += 5;

  // MACD (0-10)
  if (t.macdTrend === 'BULLISH') score += 10;

  // Price vs SMA50 (0-10)
  if (t.sma50 && price > t.sma50) score += 10;

  return score;
}

/**
 * Calculate risk score (0-15).
 * Low beta = lower risk = higher score.
 */
function calculateRiskScore(f: Fundamentals): number {
  const beta = f.beta ?? 1;

  if (beta < 1.2) return 15;
  if (beta < 1.5) return 10;
  return 5;
}

/**
 * Determine recommendation from score.
 */
function getRecommendation(score: number): Recommendation {
  if (score >= THRESHOLDS.STRONG_BUY) return 'STRONG_BUY';
  if (score >= THRESHOLDS.BUY) return 'BUY';
  if (score >= THRESHOLDS.HOLD) return 'HOLD';
  return 'SELL';
}

/**
 * Extract bull signals from data.
 */
function extractBullSignals(f: Fundamentals, t: Technicals): string[] {
  const signals: string[] = [];

  const pe = f.peRatio ?? 0;
  if (pe > 0 && pe < 15) signals.push(`Low P/E: ${pe.toFixed(1)}`);

  const div = f.dividendYield?.value ?? 0;
  if (div > 3) signals.push(`High Dividend: ${div.toFixed(1)}%`);

  if (t.rsiSignal === 'OVERSOLD') signals.push(`RSI Oversold: ${t.rsi.toFixed(0)}`);
  if (t.macdTrend === 'BULLISH') signals.push('MACD Bullish Crossover');

  const roe = f.roe?.value ?? 0;
  if (roe > 15) signals.push(`Strong ROE: ${roe.toFixed(1)}%`);

  return signals;
}

/**
 * Extract bear signals from data.
 */
function extractBearSignals(f: Fundamentals, t: Technicals): string[] {
  const signals: string[] = [];

  const pe = f.peRatio ?? 0;
  if (pe > 30) signals.push(`High P/E: ${pe.toFixed(1)}`);

  if (t.rsiSignal === 'OVERBOUGHT') signals.push(`RSI Overbought: ${t.rsi.toFixed(0)}`);

  const de = f.debtToEquity ?? 0;
  if (de > 2) signals.push(`High Debt: D/E ${de.toFixed(2)}`);

  const beta = f.beta ?? 1;
  if (beta > 1.5) signals.push(`High Beta: ${beta.toFixed(2)}`);

  return signals;
}

/**
 * Extract exchange from symbol.
 */
function getExchange(symbol: string): Exchange {
  if (symbol.endsWith('.NS')) return 'NSE';
  if (symbol.endsWith('.BO')) return 'BSE';
  if (symbol.endsWith('.L')) return 'LSE';
  if (symbol.includes('-USD')) return 'CRYPTO';
  return 'NASDAQ';
}

/**
 * Create multi-factor scorer.
 */
export function createScorer(): ScorerPort {
  return {
    score(
      symbol: string,
      fundamentals: Fundamentals,
      technicals: Technicals,
      riskProfile: RiskProfile
    ): StockScore {
      const weights = WEIGHTS[riskProfile];
      const price = technicals.sma20; // Use SMA20 as proxy for current price

      // Calculate factor scores
      const factorScores: FactorScores = {
        value: calculateValueScore(fundamentals),
        quality: calculateQualityScore(fundamentals),
        momentum: calculateMomentumScore(technicals),
        technical: calculateTechnicalScore(technicals, price),
        risk: calculateRiskScore(fundamentals),
      };

      // Weighted final score (normalize to 0-10)
      const weightedSum =
        factorScores.value * weights.value +
        factorScores.quality * weights.quality +
        factorScores.momentum * weights.momentum +
        factorScores.technical * weights.technical +
        factorScores.risk * weights.risk;

      const score = weightedSum / 3; // Normalize

      return {
        symbol,
        exchange: getExchange(symbol),
        score: Math.round(score * 100) / 100,
        recommendation: getRecommendation(score),
        factorScores,
        bullSignals: extractBullSignals(fundamentals, technicals),
        bearSignals: extractBearSignals(fundamentals, technicals),
        timestamp: new Date(),
      };
    },

    scoreAndRank(
      data: ReadonlyArray<{ symbol: string; fundamentals: Fundamentals; technicals: Technicals }>,
      riskProfile: RiskProfile
    ): readonly StockScore[] {
      return data
        .map(({ symbol, fundamentals, technicals }) =>
          this.score(symbol, fundamentals, technicals, riskProfile)
        )
        .sort((a, b) => b.score - a.score);
    },
  };
}
