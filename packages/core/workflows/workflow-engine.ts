/**
 * Simple Workflow Engine
 * ======================
 *
 * Lightweight automation engine for "if this then that" rules.
 * Ported from: FinceptTerminal/src/services/nodeSystem/
 * Simplified for: Hackathon demo - visual rule builder
 */

import type { Signal, Currency } from '../domain/types.js';

// ============================================================================
// TYPES
// ============================================================================

export type TriggerType =
  | 'price_above'
  | 'price_below'
  | 'price_change_pct'
  | 'schedule'
  | 'goal_progress'
  | 'fx_rate'
  | 'news_keyword';

export type ActionType =
  | 'notify'
  | 'buy'
  | 'sell'
  | 'rebalance'
  | 'create_alert'
  | 'webhook';

export interface WorkflowTrigger {
  type: TriggerType;
  config: Record<string, unknown>;
}

export interface WorkflowAction {
  type: ActionType;
  config: Record<string, unknown>;
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  trigger: WorkflowTrigger;
  conditions?: WorkflowCondition[];
  actions: WorkflowAction[];
  createdAt: Date;
  lastTriggeredAt?: Date;
  triggerCount: number;
}

export interface WorkflowCondition {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains';
  value: unknown;
}

export interface WorkflowContext {
  symbol?: string;
  price?: number;
  change?: number;
  goalId?: string;
  goalProgress?: number;
  fxPair?: string;
  fxRate?: number;
  newsHeadline?: string;
  [key: string]: unknown;
}

export interface WorkflowExecution {
  workflowId: string;
  triggeredAt: Date;
  context: WorkflowContext;
  actionsExecuted: string[];
  success: boolean;
  error?: string;
}

// ============================================================================
// IN-MEMORY STORAGE
// ============================================================================

const workflows: Map<string, Workflow> = new Map();
const executions: WorkflowExecution[] = [];

// ============================================================================
// WORKFLOW ENGINE
// ============================================================================

export const workflowEngine = {
  /**
   * Create a new workflow.
   */
  createWorkflow(
    name: string,
    trigger: WorkflowTrigger,
    actions: WorkflowAction[],
    options?: {
      description?: string;
      conditions?: WorkflowCondition[];
    }
  ): Workflow {
    const id = `wf-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

    const workflow: Workflow = {
      id,
      name,
      description: options?.description,
      enabled: true,
      trigger,
      conditions: options?.conditions,
      actions,
      createdAt: new Date(),
      triggerCount: 0,
    };

    workflows.set(id, workflow);
    return workflow;
  },

  /**
   * Get all workflows.
   */
  getWorkflows(): Workflow[] {
    return Array.from(workflows.values());
  },

  /**
   * Get a specific workflow.
   */
  getWorkflow(id: string): Workflow | null {
    return workflows.get(id) || null;
  },

  /**
   * Enable/disable a workflow.
   */
  setEnabled(id: string, enabled: boolean): void {
    const workflow = workflows.get(id);
    if (workflow) {
      workflow.enabled = enabled;
    }
  },

  /**
   * Delete a workflow.
   */
  deleteWorkflow(id: string): boolean {
    return workflows.delete(id);
  },

  /**
   * Check if a trigger matches the current context.
   */
  checkTrigger(trigger: WorkflowTrigger, context: WorkflowContext): boolean {
    switch (trigger.type) {
      case 'price_above':
        return (context.price ?? 0) > (trigger.config.threshold as number);

      case 'price_below':
        return (context.price ?? 0) < (trigger.config.threshold as number);

      case 'price_change_pct':
        const changePct = Math.abs(context.change ?? 0);
        return changePct >= (trigger.config.threshold as number);

      case 'goal_progress':
        return (context.goalProgress ?? 0) >= (trigger.config.milestone as number);

      case 'fx_rate':
        const fxThreshold = trigger.config.threshold as number;
        const fxDirection = trigger.config.direction as 'above' | 'below';
        if (fxDirection === 'above') {
          return (context.fxRate ?? 0) > fxThreshold;
        } else {
          return (context.fxRate ?? 0) < fxThreshold;
        }

      case 'news_keyword':
        const keywords = trigger.config.keywords as string[];
        const headline = (context.newsHeadline ?? '').toLowerCase();
        return keywords.some(kw => headline.includes(kw.toLowerCase()));

      case 'schedule':
        // Schedule triggers are handled by a cron-like system
        return true;

      default:
        return false;
    }
  },

  /**
   * Check if all conditions are met.
   */
  checkConditions(conditions: WorkflowCondition[], context: WorkflowContext): boolean {
    if (!conditions || conditions.length === 0) return true;

    return conditions.every(cond => {
      const fieldValue = context[cond.field];

      switch (cond.operator) {
        case 'eq': return fieldValue === cond.value;
        case 'ne': return fieldValue !== cond.value;
        case 'gt': return (fieldValue as number) > (cond.value as number);
        case 'lt': return (fieldValue as number) < (cond.value as number);
        case 'gte': return (fieldValue as number) >= (cond.value as number);
        case 'lte': return (fieldValue as number) <= (cond.value as number);
        case 'contains': return String(fieldValue).includes(String(cond.value));
        default: return false;
      }
    });
  },

  /**
   * Execute a workflow's actions.
   */
  async executeActions(
    actions: WorkflowAction[],
    context: WorkflowContext,
    handlers: ActionHandlers
  ): Promise<string[]> {
    const executed: string[] = [];

    for (const action of actions) {
      try {
        switch (action.type) {
          case 'notify':
            await handlers.notify?.(
              action.config.message as string,
              action.config.channels as string[]
            );
            executed.push(`notify: ${action.config.message}`);
            break;

          case 'buy':
            await handlers.buy?.(
              action.config.symbol as string,
              action.config.quantity as number,
              action.config.orderType as string
            );
            executed.push(`buy: ${action.config.quantity} ${action.config.symbol}`);
            break;

          case 'sell':
            await handlers.sell?.(
              action.config.symbol as string,
              action.config.quantity as number,
              action.config.orderType as string
            );
            executed.push(`sell: ${action.config.quantity} ${action.config.symbol}`);
            break;

          case 'rebalance':
            await handlers.rebalance?.(action.config.goalId as string);
            executed.push(`rebalance: ${action.config.goalId}`);
            break;

          case 'create_alert':
            await handlers.createAlert?.(
              action.config.symbol as string,
              action.config.condition as string,
              action.config.value as number
            );
            executed.push(`alert: ${action.config.symbol} ${action.config.condition} ${action.config.value}`);
            break;

          case 'webhook':
            await fetch(action.config.url as string, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ...context, workflow: action.config }),
            });
            executed.push(`webhook: ${action.config.url}`);
            break;
        }
      } catch (error) {
        console.error(`[Workflow] Action failed:`, action.type, error);
      }
    }

    return executed;
  },

  /**
   * Process an event against all workflows.
   */
  async processEvent(
    context: WorkflowContext,
    handlers: ActionHandlers
  ): Promise<WorkflowExecution[]> {
    const results: WorkflowExecution[] = [];

    for (const workflow of workflows.values()) {
      if (!workflow.enabled) continue;

      // Check if trigger matches
      if (!this.checkTrigger(workflow.trigger, context)) continue;

      // Check conditions
      if (!this.checkConditions(workflow.conditions || [], context)) continue;

      // Execute actions
      try {
        const actionsExecuted = await this.executeActions(
          workflow.actions,
          context,
          handlers
        );

        const execution: WorkflowExecution = {
          workflowId: workflow.id,
          triggeredAt: new Date(),
          context,
          actionsExecuted,
          success: true,
        };

        workflow.lastTriggeredAt = new Date();
        workflow.triggerCount++;

        executions.push(execution);
        results.push(execution);

        console.log(`[Workflow] Executed: ${workflow.name}`, actionsExecuted);
      } catch (error) {
        const execution: WorkflowExecution = {
          workflowId: workflow.id,
          triggeredAt: new Date(),
          context,
          actionsExecuted: [],
          success: false,
          error: String(error),
        };

        executions.push(execution);
        results.push(execution);
      }
    }

    return results;
  },

  /**
   * Get execution history.
   */
  getExecutions(workflowId?: string, limit: number = 50): WorkflowExecution[] {
    let execs = [...executions];

    if (workflowId) {
      execs = execs.filter(e => e.workflowId === workflowId);
    }

    return execs
      .sort((a, b) => b.triggeredAt.getTime() - a.triggeredAt.getTime())
      .slice(0, limit);
  },

  // ============================================================================
  // PRESET WORKFLOWS (Quick Setup for Demo)
  // ============================================================================

  /**
   * Create a price drop alert workflow.
   */
  createPriceDropAlert(
    symbol: string,
    dropPct: number,
    notifyChannels: string[] = ['push']
  ): Workflow {
    return this.createWorkflow(
      `${symbol} Drop Alert`,
      {
        type: 'price_change_pct',
        config: { threshold: dropPct, symbol },
      },
      [
        {
          type: 'notify',
          config: {
            message: `${symbol} dropped ${dropPct}%! Current price: {price}`,
            channels: notifyChannels,
          },
        },
      ],
      {
        description: `Alert when ${symbol} drops ${dropPct}% or more`,
        conditions: [{ field: 'symbol', operator: 'eq', value: symbol }],
      }
    );
  },

  /**
   * Create a DCA (Dollar Cost Average) workflow.
   */
  createDCAWorkflow(
    symbol: string,
    amount: number,
    currency: Currency,
    frequency: 'daily' | 'weekly' | 'monthly'
  ): Workflow {
    return this.createWorkflow(
      `DCA ${symbol}`,
      {
        type: 'schedule',
        config: { frequency },
      },
      [
        {
          type: 'buy',
          config: {
            symbol,
            quantity: 'auto', // Calculate based on amount
            amount,
            currency,
            orderType: 'MARKET',
          },
        },
        {
          type: 'notify',
          config: {
            message: `DCA executed: Bought ${symbol} for ${currency} ${amount}`,
            channels: ['push'],
          },
        },
      ],
      {
        description: `Auto-invest ${currency} ${amount} in ${symbol} ${frequency}`,
      }
    );
  },

  /**
   * Create a goal milestone workflow.
   */
  createGoalMilestoneWorkflow(
    goalId: string,
    goalName: string,
    milestones: number[] = [25, 50, 75, 100]
  ): Workflow[] {
    return milestones.map(milestone =>
      this.createWorkflow(
        `${goalName} ${milestone}% Milestone`,
        {
          type: 'goal_progress',
          config: { goalId, milestone },
        },
        [
          {
            type: 'notify',
            config: {
              message: `Congratulations! Your "${goalName}" goal is ${milestone}% complete!`,
              channels: ['push', 'email'],
            },
          },
        ],
        {
          description: `Celebrate ${milestone}% progress on ${goalName}`,
          conditions: [{ field: 'goalId', operator: 'eq', value: goalId }],
        }
      )
    );
  },

  /**
   * Create an FX alert workflow.
   */
  createFxAlertWorkflow(
    pair: string,
    targetRate: number,
    direction: 'above' | 'below'
  ): Workflow {
    return this.createWorkflow(
      `FX Alert: ${pair} ${direction} ${targetRate}`,
      {
        type: 'fx_rate',
        config: { pair, threshold: targetRate, direction },
      },
      [
        {
          type: 'notify',
          config: {
            message: `FX Alert: ${pair} is now ${direction} ${targetRate}. Good time to transfer!`,
            channels: ['push', 'sms'],
          },
        },
      ],
      {
        description: `Alert when ${pair} goes ${direction} ${targetRate}`,
        conditions: [{ field: 'fxPair', operator: 'eq', value: pair }],
      }
    );
  },

  /**
   * Create a rebalance workflow.
   */
  createRebalanceWorkflow(
    goalId: string,
    driftThreshold: number = 5
  ): Workflow {
    return this.createWorkflow(
      `Auto-Rebalance Goal`,
      {
        type: 'price_change_pct',
        config: { threshold: driftThreshold },
      },
      [
        {
          type: 'rebalance',
          config: { goalId },
        },
        {
          type: 'notify',
          config: {
            message: `Portfolio rebalanced for goal. Drift was {driftPct}%.`,
            channels: ['push'],
          },
        },
      ],
      {
        description: `Auto-rebalance when allocation drifts ${driftThreshold}%+`,
      }
    );
  },
};

// ============================================================================
// ACTION HANDLERS INTERFACE
// ============================================================================

export interface ActionHandlers {
  notify?: (message: string, channels: string[]) => Promise<void>;
  buy?: (symbol: string, quantity: number, orderType: string) => Promise<void>;
  sell?: (symbol: string, quantity: number, orderType: string) => Promise<void>;
  rebalance?: (goalId: string) => Promise<void>;
  createAlert?: (symbol: string, condition: string, value: number) => Promise<void>;
}
