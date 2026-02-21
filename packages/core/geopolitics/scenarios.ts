/**
 * Geopolitical Scenarios
 * ======================
 *
 * Based on "Prisoners of Geography" and "The Grand Chessboard".
 * Maps world events to sector impacts, stock recommendations, and currency effects.
 *
 * Ported from: FinceptTerminal/voltagent/src/core/geopolitics/scenarios.ts
 * Enhanced with: Currency impact for cross-border users
 */

import type { GeopoliticalScenario, Market, Currency } from '../domain/types.js';
import type { GeopoliticsPort } from '../domain/interfaces.js';

const SCENARIOS: readonly GeopoliticalScenario[] = [
  {
    id: 'china-taiwan',
    name: 'China-Taiwan Tensions',
    framework: 'prisoners-of-geography',
    triggerWords: ['taiwan', 'china tension', 'strait crisis', 'chip war', 'semiconductor blockade'],
    bullishSectors: ['Defense', 'Cybersecurity', 'Domestic Semiconductor', 'Gold'],
    bearishSectors: ['Consumer Electronics', 'Shipping', 'Luxury Goods', 'China ADRs'],
    stocks: {
      india: ['HAL.NS', 'BEL.NS', 'HINDPETRO.NS', 'ONGC.NS'],
      us: ['LMT', 'RTX', 'NOC', 'GD', 'PANW', 'CRWD'],
      uk: ['BAE.L', 'RR.L'],
      uae: [],
      singapore: ['ST.SI'],
      crypto: ['BTC-USD', 'ETH-USD'],
    },
    currencyImpact: {
      INR: -0.05,   // Slight negative (risk-off)
      USD: 0.10,    // Safe haven
      AED: 0.02,    // Slight positive (oil)
      GBP: -0.03,
      EUR: -0.05,
      SGD: -0.08,   // Negative (regional)
      CAD: 0.02,
      AUD: -0.10,   // Negative (China exposure)
    } as Record<Currency, number>,
  },
  {
    id: 'russia-nato',
    name: 'Russia-NATO Escalation',
    framework: 'grand-chessboard',
    triggerWords: ['russia', 'nato', 'ukraine', 'european war', 'energy crisis'],
    bullishSectors: ['Energy', 'Defense', 'Agriculture', 'Gold'],
    bearishSectors: ['European Banks', 'Travel', 'Luxury', 'Auto'],
    stocks: {
      india: ['ONGC.NS', 'RELIANCE.NS', 'GAIL.NS', 'COALINDIA.NS'],
      us: ['XOM', 'CVX', 'OXY', 'LMT', 'RTX', 'ADM', 'GLD'],
      uk: ['BP.L', 'SHEL.L'],
      uae: ['ADNOCDIST.AD'],
      singapore: [],
      crypto: ['BTC-USD'],
    },
    currencyImpact: {
      INR: -0.03,
      USD: 0.15,    // Strong safe haven
      AED: 0.08,    // Oil positive
      GBP: -0.10,   // Negative (proximity)
      EUR: -0.15,   // Strong negative
      SGD: 0.02,
      CAD: 0.05,    // Oil positive
      AUD: 0.03,
    } as Record<Currency, number>,
  },
  {
    id: 'middle-east',
    name: 'Middle East Conflict',
    framework: 'prisoners-of-geography',
    triggerWords: ['iran', 'israel', 'saudi', 'oil crisis', 'strait of hormuz', 'opec', 'gaza', 'hezbollah'],
    bullishSectors: ['Oil & Gas', 'Defense', 'Solar', 'Gold'],
    bearishSectors: ['Airlines', 'Travel', 'Consumer Discretionary'],
    stocks: {
      india: ['RELIANCE.NS', 'ONGC.NS', 'BPCL.NS', 'IOC.NS'],
      us: ['XOM', 'CVX', 'SLB', 'HAL', 'FSLR', 'ENPH'],
      uk: ['BP.L', 'SHEL.L'],
      uae: [],  // Reduce exposure
      singapore: [],
      crypto: ['BTC-USD', 'ETH-USD'],
    },
    currencyImpact: {
      INR: -0.08,   // Negative (oil importer)
      USD: 0.10,
      AED: -0.05,   // Negative (regional risk)
      GBP: -0.02,
      EUR: -0.05,
      SGD: -0.02,
      CAD: 0.08,    // Oil positive
      AUD: 0.02,
    } as Record<Currency, number>,
  },
  {
    id: 'india-china',
    name: 'India-China Border Tensions',
    framework: 'prisoners-of-geography',
    triggerWords: ['ladakh', 'galwan', 'india china', 'border clash', 'lac tension', 'arunachal'],
    bullishSectors: ['Indian Defense', 'Indian IT', 'Domestic Manufacturing'],
    bearishSectors: ['Chinese Imports', 'Electronics'],
    stocks: {
      india: ['HAL.NS', 'BEL.NS', 'BHARATFORG.NS', 'TCS.NS', 'INFY.NS'],
      us: ['LMT', 'BA', 'GD'],
      uk: [],
      uae: [],
      singapore: [],
      crypto: [],
    },
    currencyImpact: {
      INR: -0.05,
      USD: 0.05,
      AED: 0.02,
      GBP: 0.00,
      EUR: 0.00,
      SGD: -0.02,
      CAD: 0.00,
      AUD: -0.03,
    } as Record<Currency, number>,
  },
  {
    id: 'dollar-dedollarization',
    name: 'De-dollarization Trend',
    framework: 'grand-chessboard',
    triggerWords: ['dedollarization', 'brics currency', 'dollar collapse', 'yuan', 'gold standard', 'brics'],
    bullishSectors: ['Gold', 'Commodities', 'Crypto', 'Emerging Markets'],
    bearishSectors: ['US Banks', 'US Treasury', 'Dollar-denominated Debt'],
    stocks: {
      india: ['GOLDBEES.NS', 'TITAN.NS', 'RELIANCE.NS'],
      us: ['GLD', 'SLV', 'GOLD', 'NEM', 'FCX'],
      uk: ['GLEN.L', 'RIO.L'],
      uae: [],
      singapore: [],
      crypto: ['BTC-USD', 'ETH-USD', 'XRP-USD'],
    },
    currencyImpact: {
      INR: 0.05,    // Positive (diversification)
      USD: -0.15,   // Strong negative
      AED: 0.08,    // Positive (gold reserves)
      GBP: 0.02,
      EUR: 0.05,
      SGD: 0.03,
      CAD: 0.03,
      AUD: 0.05,
    } as Record<Currency, number>,
  },
  {
    id: 'climate-energy',
    name: 'Climate/Energy Transition',
    framework: 'prisoners-of-geography',
    triggerWords: ['climate', 'renewable', 'ev transition', 'carbon tax', 'green energy', 'net zero', 'cop28'],
    bullishSectors: ['Solar', 'EV', 'Battery', 'Green Hydrogen'],
    bearishSectors: ['Coal', 'Traditional Oil', 'Legacy Auto'],
    stocks: {
      india: ['TATAPOWER.NS', 'ADANIGREEN.NS', 'SUZLON.NS', 'TATAMOTORS.NS'],
      us: ['TSLA', 'RIVN', 'FSLR', 'ENPH', 'PLUG', 'NEE'],
      uk: ['SSE.L', 'NG.L'],
      uae: ['MASDAR'],  // Clean energy
      singapore: [],
      crypto: [],
    },
    currencyImpact: {
      INR: 0.00,
      USD: -0.02,
      AED: -0.05,   // Negative (oil transition)
      GBP: 0.02,
      EUR: 0.03,    // Positive (green leadership)
      SGD: 0.02,
      CAD: -0.03,   // Negative (oil)
      AUD: 0.05,    // Positive (mining/lithium)
    } as Record<Currency, number>,
  },
  {
    id: 'fed-rate-cycle',
    name: 'Fed Rate Pivot',
    framework: 'macro-economics',
    triggerWords: ['fed rate', 'interest rate', 'jerome powell', 'rate cut', 'rate hike', 'fomc'],
    bullishSectors: ['Growth Tech', 'Real Estate', 'High-Dividend'],
    bearishSectors: ['Banks', 'Insurance'],
    stocks: {
      india: ['HDFC.NS', 'ICICIBANK.NS', 'SBIN.NS'],
      us: ['QQQ', 'VNQ', 'XLU', 'MSFT', 'GOOGL'],
      uk: ['LAND.L'],
      uae: [],
      singapore: ['C31.SI', 'D05.SI'],
      crypto: ['BTC-USD', 'ETH-USD'],
    },
    currencyImpact: {
      INR: 0.05,    // Positive on rate cuts
      USD: -0.08,   // Negative on rate cuts
      AED: 0.00,    // Pegged
      GBP: 0.03,
      EUR: 0.03,
      SGD: 0.02,
      CAD: 0.02,
      AUD: 0.03,
    } as Record<Currency, number>,
  },
] as const;

/**
 * Create geopolitics engine.
 */
export function createGeopoliticsEngine(): GeopoliticsPort {
  return {
    getScenarios(): readonly GeopoliticalScenario[] {
      return SCENARIOS;
    },

    detectScenario(input: string): GeopoliticalScenario | null {
      const lower = input.toLowerCase();

      for (const scenario of SCENARIOS) {
        for (const trigger of scenario.triggerWords) {
          if (lower.includes(trigger)) {
            return scenario;
          }
        }
      }

      return null;
    },

    getStocksForScenario(
      scenarioId: string,
      markets: readonly Market[]
    ): readonly string[] {
      const scenario = SCENARIOS.find((s) => s.id === scenarioId);
      if (!scenario) return [];

      const stocks: string[] = [];
      for (const market of markets) {
        stocks.push(...scenario.stocks[market]);
      }

      return stocks;
    },

    getCurrencyImpact(scenarioId: string): Record<Currency, number> {
      const scenario = SCENARIOS.find((s) => s.id === scenarioId);
      if (!scenario) return {} as Record<Currency, number>;

      return scenario.currencyImpact;
    },
  };
}

/**
 * Detect multiple active scenarios from news/input.
 */
export function detectActiveScenarios(newsItems: string[]): GeopoliticalScenario[] {
  const engine = createGeopoliticsEngine();
  const detected = new Set<string>();
  const scenarios: GeopoliticalScenario[] = [];

  for (const news of newsItems) {
    const scenario = engine.detectScenario(news);
    if (scenario && !detected.has(scenario.id)) {
      detected.add(scenario.id);
      scenarios.push(scenario);
    }
  }

  return scenarios;
}

/**
 * Calculate net currency impact from multiple active scenarios.
 */
export function calculateNetCurrencyImpact(
  activeScenarios: GeopoliticalScenario[]
): Record<Currency, number> {
  const impact: Record<Currency, number> = {
    INR: 0, USD: 0, AED: 0, GBP: 0, EUR: 0, SGD: 0, CAD: 0, AUD: 0,
  };

  for (const scenario of activeScenarios) {
    for (const [currency, delta] of Object.entries(scenario.currencyImpact)) {
      impact[currency as Currency] += delta;
    }
  }

  // Normalize if multiple scenarios
  if (activeScenarios.length > 1) {
    for (const currency of Object.keys(impact) as Currency[]) {
      impact[currency] /= activeScenarios.length;
    }
  }

  return impact;
}
