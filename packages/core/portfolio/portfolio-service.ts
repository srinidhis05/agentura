/**
 * Portfolio Service
 * =================
 *
 * Track holdings, transactions, and performance across multiple portfolios.
 * Ported from: FinceptTerminal/src/services/portfolio/portfolioService.ts
 * Enhanced with: Multi-currency support for cross-border users
 */

import type {
  Portfolio,
  Position,
  Money,
  Currency,
  Exchange,
  Percentage,
} from '../domain/types.js';

// ============================================================================
// TYPES
// ============================================================================

export interface Transaction {
  id: string;
  portfolioId: string;
  symbol: string;
  exchange: Exchange;
  type: 'BUY' | 'SELL' | 'DIVIDEND' | 'SPLIT' | 'TRANSFER_IN' | 'TRANSFER_OUT';
  quantity: number;
  price: number;
  currency: Currency;
  fees: number;
  date: Date;
  notes?: string;
}

export interface PortfolioSummary {
  id: string;
  name: string;
  baseCurrency: Currency;
  totalValue: Money;
  totalCost: Money;
  unrealizedPnl: Money;
  unrealizedPnlPct: Percentage;
  realizedPnl: Money;
  positionCount: number;
  lastUpdated: Date;
}

export interface PerformanceSnapshot {
  date: Date;
  totalValue: Money;
  dailyPnl: Money;
  dailyPnlPct: Percentage;
  cumulativePnl: Money;
  cumulativePnlPct: Percentage;
}

export interface HoldingSummary {
  symbol: string;
  exchange: Exchange;
  quantity: number;
  avgCostBasis: number;
  currentPrice: number;
  marketValue: Money;
  unrealizedPnl: Money;
  unrealizedPnlPct: Percentage;
  weight: Percentage;
  currency: Currency;
}

// ============================================================================
// IN-MEMORY STORAGE (Replace with database in production)
// ============================================================================

const portfolios: Map<string, PortfolioSummary> = new Map();
const transactions: Map<string, Transaction[]> = new Map();
const holdings: Map<string, HoldingSummary[]> = new Map();
const snapshots: Map<string, PerformanceSnapshot[]> = new Map();

// ============================================================================
// PORTFOLIO SERVICE
// ============================================================================

export const portfolioService = {
  /**
   * Create a new portfolio.
   */
  createPortfolio(
    name: string,
    baseCurrency: Currency = 'INR'
  ): PortfolioSummary {
    const id = `portfolio-${Date.now()}`;
    const portfolio: PortfolioSummary = {
      id,
      name,
      baseCurrency,
      totalValue: { amount: 0, currency: baseCurrency },
      totalCost: { amount: 0, currency: baseCurrency },
      unrealizedPnl: { amount: 0, currency: baseCurrency },
      unrealizedPnlPct: { value: 0 },
      realizedPnl: { amount: 0, currency: baseCurrency },
      positionCount: 0,
      lastUpdated: new Date(),
    };

    portfolios.set(id, portfolio);
    transactions.set(id, []);
    holdings.set(id, []);
    snapshots.set(id, []);

    return portfolio;
  },

  /**
   * Get all portfolios for a user.
   */
  getPortfolios(): PortfolioSummary[] {
    return Array.from(portfolios.values());
  },

  /**
   * Get a specific portfolio.
   */
  getPortfolio(portfolioId: string): PortfolioSummary | null {
    return portfolios.get(portfolioId) || null;
  },

  /**
   * Add a transaction to a portfolio.
   */
  addTransaction(tx: Omit<Transaction, 'id'>): Transaction {
    const id = `tx-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const transaction: Transaction = { id, ...tx };

    const txList = transactions.get(tx.portfolioId) || [];
    txList.push(transaction);
    transactions.set(tx.portfolioId, txList);

    // Update holdings
    this.recalculateHoldings(tx.portfolioId);

    return transaction;
  },

  /**
   * Get transactions for a portfolio.
   */
  getTransactions(
    portfolioId: string,
    filter?: {
      symbol?: string;
      type?: Transaction['type'];
      startDate?: Date;
      endDate?: Date;
    }
  ): Transaction[] {
    let txList = transactions.get(portfolioId) || [];

    if (filter) {
      if (filter.symbol) {
        txList = txList.filter((tx) => tx.symbol === filter.symbol);
      }
      if (filter.type) {
        txList = txList.filter((tx) => tx.type === filter.type);
      }
      if (filter.startDate) {
        txList = txList.filter((tx) => tx.date >= filter.startDate!);
      }
      if (filter.endDate) {
        txList = txList.filter((tx) => tx.date <= filter.endDate!);
      }
    }

    return txList.sort((a, b) => b.date.getTime() - a.date.getTime());
  },

  /**
   * Get holdings for a portfolio.
   */
  getHoldings(portfolioId: string): HoldingSummary[] {
    return holdings.get(portfolioId) || [];
  },

  /**
   * Recalculate holdings from transactions.
   */
  recalculateHoldings(portfolioId: string): void {
    const txList = transactions.get(portfolioId) || [];
    const portfolio = portfolios.get(portfolioId);
    if (!portfolio) return;

    // Group transactions by symbol
    const bySymbol = new Map<string, Transaction[]>();
    for (const tx of txList) {
      const list = bySymbol.get(tx.symbol) || [];
      list.push(tx);
      bySymbol.set(tx.symbol, list);
    }

    // Calculate holdings for each symbol
    const newHoldings: HoldingSummary[] = [];
    let totalValue = 0;
    let totalCost = 0;

    for (const [symbol, txs] of bySymbol) {
      let quantity = 0;
      let costBasis = 0;

      for (const tx of txs.sort((a, b) => a.date.getTime() - b.date.getTime())) {
        if (tx.type === 'BUY' || tx.type === 'TRANSFER_IN') {
          costBasis = (costBasis * quantity + tx.price * tx.quantity) / (quantity + tx.quantity);
          quantity += tx.quantity;
        } else if (tx.type === 'SELL' || tx.type === 'TRANSFER_OUT') {
          quantity -= tx.quantity;
        } else if (tx.type === 'SPLIT') {
          // Handle stock splits (tx.quantity is the split ratio, e.g., 2 for 2:1)
          quantity *= tx.quantity;
          costBasis /= tx.quantity;
        }
      }

      if (quantity > 0) {
        const lastTx = txs[txs.length - 1];
        const currentPrice = lastTx.price; // In real app, fetch live price
        const marketValue = quantity * currentPrice;
        const unrealizedPnl = marketValue - quantity * costBasis;

        totalValue += marketValue;
        totalCost += quantity * costBasis;

        newHoldings.push({
          symbol,
          exchange: lastTx.exchange,
          quantity,
          avgCostBasis: costBasis,
          currentPrice,
          marketValue: { amount: marketValue, currency: lastTx.currency },
          unrealizedPnl: { amount: unrealizedPnl, currency: lastTx.currency },
          unrealizedPnlPct: { value: (unrealizedPnl / (quantity * costBasis)) * 100 },
          weight: { value: 0 }, // Will be calculated after totals
          currency: lastTx.currency,
        });
      }
    }

    // Calculate weights
    for (const h of newHoldings) {
      h.weight.value = totalValue > 0 ? (h.marketValue.amount / totalValue) * 100 : 0;
    }

    holdings.set(portfolioId, newHoldings);

    // Update portfolio summary
    portfolio.totalValue = { amount: totalValue, currency: portfolio.baseCurrency };
    portfolio.totalCost = { amount: totalCost, currency: portfolio.baseCurrency };
    portfolio.unrealizedPnl = { amount: totalValue - totalCost, currency: portfolio.baseCurrency };
    portfolio.unrealizedPnlPct = { value: totalCost > 0 ? ((totalValue - totalCost) / totalCost) * 100 : 0 };
    portfolio.positionCount = newHoldings.length;
    portfolio.lastUpdated = new Date();

    portfolios.set(portfolioId, portfolio);
  },

  /**
   * Update prices for all holdings.
   */
  async updatePrices(
    portfolioId: string,
    prices: Map<string, number>
  ): Promise<void> {
    const holdingList = holdings.get(portfolioId);
    if (!holdingList) return;

    let totalValue = 0;
    let totalCost = 0;

    for (const h of holdingList) {
      const newPrice = prices.get(h.symbol);
      if (newPrice !== undefined) {
        h.currentPrice = newPrice;
        h.marketValue.amount = h.quantity * newPrice;
        h.unrealizedPnl.amount = h.marketValue.amount - h.quantity * h.avgCostBasis;
        h.unrealizedPnlPct.value = (h.unrealizedPnl.amount / (h.quantity * h.avgCostBasis)) * 100;
      }
      totalValue += h.marketValue.amount;
      totalCost += h.quantity * h.avgCostBasis;
    }

    // Recalculate weights
    for (const h of holdingList) {
      h.weight.value = totalValue > 0 ? (h.marketValue.amount / totalValue) * 100 : 0;
    }

    // Update portfolio summary
    const portfolio = portfolios.get(portfolioId);
    if (portfolio) {
      portfolio.totalValue.amount = totalValue;
      portfolio.unrealizedPnl.amount = totalValue - totalCost;
      portfolio.unrealizedPnlPct.value = totalCost > 0 ? ((totalValue - totalCost) / totalCost) * 100 : 0;
      portfolio.lastUpdated = new Date();
    }
  },

  /**
   * Take a performance snapshot.
   */
  takeSnapshot(portfolioId: string): PerformanceSnapshot | null {
    const portfolio = portfolios.get(portfolioId);
    if (!portfolio) return null;

    const snapshotList = snapshots.get(portfolioId) || [];
    const lastSnapshot = snapshotList[snapshotList.length - 1];

    const dailyPnl = lastSnapshot
      ? portfolio.totalValue.amount - lastSnapshot.totalValue.amount
      : 0;

    const snapshot: PerformanceSnapshot = {
      date: new Date(),
      totalValue: { ...portfolio.totalValue },
      dailyPnl: { amount: dailyPnl, currency: portfolio.baseCurrency },
      dailyPnlPct: {
        value: lastSnapshot && lastSnapshot.totalValue.amount > 0
          ? (dailyPnl / lastSnapshot.totalValue.amount) * 100
          : 0,
      },
      cumulativePnl: { ...portfolio.unrealizedPnl },
      cumulativePnlPct: { ...portfolio.unrealizedPnlPct },
    };

    snapshotList.push(snapshot);
    snapshots.set(portfolioId, snapshotList);

    return snapshot;
  },

  /**
   * Get performance history.
   */
  getPerformanceHistory(
    portfolioId: string,
    days: number = 30
  ): PerformanceSnapshot[] {
    const snapshotList = snapshots.get(portfolioId) || [];
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    return snapshotList.filter((s) => s.date >= cutoff);
  },

  /**
   * Get sector/asset allocation.
   */
  getAllocation(portfolioId: string): Record<string, Percentage> {
    const holdingList = holdings.get(portfolioId) || [];
    const allocation: Record<string, number> = {};

    for (const h of holdingList) {
      // Group by exchange as a proxy for asset class
      const key = h.exchange;
      allocation[key] = (allocation[key] || 0) + h.weight.value;
    }

    const result: Record<string, Percentage> = {};
    for (const [key, value] of Object.entries(allocation)) {
      result[key] = { value };
    }

    return result;
  },

  /**
   * Get currency exposure.
   */
  getCurrencyExposure(portfolioId: string): Record<Currency, Percentage> {
    const holdingList = holdings.get(portfolioId) || [];
    const exposure: Record<string, number> = {};

    for (const h of holdingList) {
      exposure[h.currency] = (exposure[h.currency] || 0) + h.weight.value;
    }

    const result: Record<Currency, Percentage> = {} as Record<Currency, Percentage>;
    for (const [key, value] of Object.entries(exposure)) {
      result[key as Currency] = { value };
    }

    return result;
  },
};
