/**
 * Core Package Exports
 * ====================
 *
 * Clean Architecture core with zero external dependencies.
 * Ported from FinceptTerminal with cross-border enhancements.
 */

// Domain Types
export * from './domain/types.js';
export * from './domain/interfaces.js';

// Risk Management (Moat #2)
export { createRiskManager, requiresHumanApproval, getRiskStatus } from './risk/risk-manager.js';

// Scoring
export { createScorer } from './scoring/scorer.js';

// Geopolitics
export {
  createGeopoliticsEngine,
  detectActiveScenarios,
  calculateNetCurrencyImpact,
} from './geopolitics/scenarios.js';

// Portfolio Service
export {
  portfolioService,
  type Transaction,
  type PortfolioSummary,
  type PerformanceSnapshot,
  type HoldingSummary,
} from './portfolio/portfolio-service.js';

// Notification Service
export {
  notificationService,
  type Notification,
  type NotificationChannel,
  type NotificationPreferences,
  type NotificationType,
  type ChannelConfig,
} from './notifications/notification-service.js';

// Workflow Engine
export {
  workflowEngine,
  type Workflow,
  type WorkflowTrigger,
  type WorkflowAction,
  type WorkflowCondition,
  type WorkflowContext,
  type WorkflowExecution,
  type ActionHandlers,
} from './workflows/workflow-engine.js';
