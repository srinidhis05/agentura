---
name: loss-limit
description: Enforce daily and weekly loss limits with circuit breakers
triggers:
  - "check loss limit"
  - "daily loss"
  - "circuit breaker"
  - "halt trading"
---

# Loss Limit Skill

> You enforce loss limits. When limits are hit, trading STOPS. No exceptions.

## Hard Limits (Non-Negotiable)

| Limit | Threshold | Action |
|-------|-----------|--------|
| Daily Loss | 5% | Halt all trading for rest of day |
| Weekly Loss | 10% | Halt + require manual reset |
| Max Drawdown | 15% | Reduce all positions 50% |
| Consecutive Losses | 3 trades | Pause 1 hour |

## Checking Loss Status

Before ANY trade, check:

```typescript
const dailyLossPct = Math.abs(dailyPnl / portfolioValue) * 100;
const weeklyLossPct = Math.abs(weeklyPnl / portfolioValue) * 100;

if (dailyLossPct >= 5.0) {
  return { blocked: true, reason: "Daily loss limit reached" };
}
```

## Circuit Breaker Activation

When triggered:

1. **Log the event** - Record in risk_events table
2. **Notify user** - Push notification + email
3. **Cancel pending orders** - All open orders cancelled
4. **Set resume time** - Auto-resume after cooling period

```json
{
  "event": "circuit_breaker_triggered",
  "reason": "daily_loss_limit",
  "loss_pct": 5.2,
  "halted_at": "2024-02-14T15:30:00Z",
  "resumes_at": "2024-02-15T09:15:00Z",
  "actions_taken": [
    "cancelled_pending_orders",
    "notified_user",
    "logged_risk_event"
  ]
}
```

## Warning Thresholds

| Warning Level | Threshold | Action |
|---------------|-----------|--------|
| Yellow | 3% daily loss | Notify user |
| Orange | 4% daily loss | Reduce position sizes 50% |
| Red | 5% daily loss | HALT |

## User Communication

When approaching limits:

```
⚠️ Loss Warning

Your portfolio is down 3.8% today.

At 5% loss, trading will automatically halt for the rest of the day.
This protects you from emotional decisions during drawdowns.

Current status: 1.2% remaining until circuit breaker.
```

When halted:

```
🛑 Trading Halted

Daily loss limit reached (-5.2%).

Trading will resume: Tomorrow at market open
Reason: Protecting your capital during drawdown

What happened:
- 4 trades today, 3 losses
- Largest loss: INFY (-2.1%)

This is normal. Even the best strategies have losing days.
Take a break and review tomorrow with fresh eyes.
```

## Guardrails

1. **NEVER** override loss limits, even if user requests
2. **NEVER** allow trades when circuit breaker is active
3. **ALWAYS** log the full portfolio state when triggered
4. **ALWAYS** notify user immediately on halt
5. **NEVER** auto-reset weekly circuit breaker (requires user action)
