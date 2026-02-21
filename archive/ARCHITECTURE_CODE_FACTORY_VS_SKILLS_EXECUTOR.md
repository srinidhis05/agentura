# Code Factory vs Skills Executor: Complementary Architectures

**Question**: How does the Code Factory approach differ from the Skills Executor (OpenClaw-style) platform we designed for ECM/FinCrime?

**Answer**: They serve DIFFERENT purposes and are COMPLEMENTARY, not competing architectures.

---

## The Core Distinction

| Dimension | Code Factory | Skills Executor |
|-----------|-------------|-----------------|
| **Purpose** | BUILD-TIME automation | RUN-TIME execution |
| **What it does** | Generates standalone products | Executes agent skills for users |
| **When it runs** | During development (CI/CD pipeline) | In production (serving user requests) |
| **Output** | FastAPI services, React apps, databases | Agent responses to Slack/WhatsApp messages |
| **Users** | Engineering team | End users (ECM field agents, FinCrime analysts) |
| **Critical path** | NO (dev tooling failure = slower dev) | YES (executor failure = users blocked) |

---

## Two Valid Use Cases (Both Needed)

### Use Case 1: Skills Executor for Internal Operations (ECM, FinCrime)

**When to Use**: Internal teams need real-time agent assistance with operational workflows

**Example Domains**:
- **ECM Operations** — Field agents ask "show my tickets", "escalate shipment stuck in Dubai"
- **FinCrime Alerts** — Analysts ask "investigate alert #5678", "show pending sanctions matches"
- **Fraud Guardian** — Risk teams ask "simulate rule change", "explain false positive"

**Architecture**:
```
User (Slack) → Skills Executor Platform → Pydantic AI Agent → executes skill → returns response
                     ↓
              aspora.config.yaml (domain registry)
                     ↓
              skills/field/my-tickets.md
```

**Characteristics**:
- **Shared runtime** — One SkillExecutor serves all users (context injection for multi-tenancy)
- **Real-time execution** — Agent runs skill logic on-demand
- **Production-critical** — If executor fails, operations teams are blocked
- **Internal only** — Not customer-facing (ops teams, analysts)

**Why Skills Executor for ECM/FinCrime**:
1. ✅ **Dynamic workflows** — "Show tickets assigned to me" requires real-time user context
2. ✅ **Low latency** — Sub-second responses (Haiku for simple lookups)
3. ✅ **Collaborative** — Team-scoped data (FinCrime queue shared across analysts)
4. ✅ **Rapid iteration** — Add new skill = drop markdown file, no deployment
5. ✅ **Cost-efficient** — Shared runtime (not per-user instances)

---

### Use Case 2: Code Factory for Building Products (Wealth, eventually ECM standalone)

**When to Use**: Generate customer-facing products or standalone services

**Example Products**:
- **Wealth Copilot** — Retail investors managing portfolios (10K+ users, needs isolation)
- **ECM SaaS** — Shipping companies buying ECM as standalone product (not internal tool)
- **Risk API** — Position sizing service sold as API (not skill)

**Architecture**:
```
Product Manager writes spec.md → Code Factory Agent → generates FastAPI service → deploys to production

Code Factory loop:
1. Coding Agent (Claude Opus) reads spec → generates code
2. Risk Policy Gate checks changed files → assigns tier
3. Code Review Agent (Greptile) scans for issues
4. Remediation Agent auto-fixes findings
5. GitHub Actions deploys if tier=low/medium, human review if critical
```

**Characteristics**:
- **Build-time** — Runs during CI/CD, not production runtime
- **Generates standalone services** — FastAPI app, React frontend, separate deployment
- **Customer-facing** — Serves external users (retail investors, shipping companies)
- **Isolated** — Each product is independent (blast radius contained)

**Why Code Factory for Wealth**:
1. ✅ **Blast radius isolation** — Portfolio bug doesn't break ECM
2. ✅ **Independent scaling** — Wealth traffic spike doesn't affect FinCrime
3. ✅ **Customization** — Retail investors need different UX than ops teams
4. ✅ **Monetization** — Can sell Wealth as standalone SaaS (clear boundaries)
5. ✅ **Compliance** — Easier audit when portfolio service is isolated

---

## The Brilliant Insight: They Coexist

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  CODE FACTORY (Build-Time)                                  │
│  - Coding Agent writes FastAPI services                     │
│  - Review Agent validates code                              │
│  - Risk Policy Gates tiered merge rules                     │
│  - Deploys BOTH customer products AND platform components   │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ generates & maintains
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  SKILLS EXECUTOR PLATFORM (Run-Time)                        │
│  - SkillExecutor with Pydantic AI                           │
│  - Domain registry (aspora.config.yaml)                     │
│  - Context injection (user_id, team_id)                     │
│  - Slack/WhatsApp adapters                                  │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ executes skills for
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  INTERNAL OPERATIONS TEAMS                                  │
│  - ECM field agents (Sarah asks "show my tickets")          │
│  - FinCrime analysts (Raj investigates alerts)              │
│  - Fraud teams (simulate rule changes)                      │
└─────────────────────────────────────────────────────────────┘

         PLUS (generated by Code Factory)
         ↓
┌─────────────────────────────────────────────────────────────┐
│  CUSTOMER-FACING PRODUCTS (Standalone FastAPI services)     │
│  - Wealth Copilot API (retail investors)                    │
│  - ECM SaaS (shipping companies)                            │
│  - Risk API (position sizing service)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Example: ECM Domain in Both Models

### Scenario 1: ECM as Skills Executor Domain (Internal Operations)

**Use Case**: Your operations team tracks shipments, resolves payment issues

**Implementation**:
```yaml
# domains/ecm/aspora.config.yaml
domain:
  name: ecm
  description: ECM Operations for internal teams
  scope: team
  owner: operations-team

skills:
  - name: my-tickets
    path: skills/field/my-tickets.md
    requires_context: [user_id, team_id]
    model: anthropic/claude-haiku-4.5

  - name: escalate-shipment
    path: skills/field/escalate-shipment.md
    requires_context: [user_id, team_id, ticket_id]
    model: anthropic/claude-sonnet-4.5
```

**User Experience**:
```
Sarah (Field Agent) on Slack: "show my tickets"
Bot: 📋 Your Tickets (5 pending)
     - #1234 Stuck shipment (Dubai → Mumbai)
     - #1235 Payment failure (beneficiary mismatch)
     ...

Sarah: "escalate ticket 1234"
Bot: 🚀 Escalated to Manager
     Priority: HIGH
     Reason: Stuck in customs >48hrs
```

**Deployment**: Skills Executor platform (shared runtime, context injection)

---

### Scenario 2: ECM as Code Factory Product (Customer-Facing SaaS)

**Use Case**: Shipping companies BUY your ECM product as standalone service

**Implementation**:
```python
# Generated by Code Factory from spec.md
# ecm-product/api/v1/tickets.py
from fastapi import APIRouter, Depends
from services.ecm_service import ECMService

router = APIRouter()

@router.get("/tickets/assigned")
async def get_assigned_tickets(
    user_id: str = Depends(get_current_user),
    team_id: str = Depends(get_user_team)
):
    """Show tickets assigned to user"""
    service = ECMService()
    tickets = service.get_my_tickets(user_id, team_id)
    return {"tickets": tickets, "count": len(tickets)}

@router.post("/tickets/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: str,
    user_id: str = Depends(get_current_user)
):
    """Escalate ticket to manager"""
    service = ECMService()
    result = service.escalate(ticket_id, user_id)
    return result
```

**User Experience**:
```
Shipping Company X uses ECM SaaS:
- React frontend at ecm.aspora.io
- REST API backend (FastAPI)
- Multi-tenant database (customer_id isolation)
- SSO login (Okta, Google Workspace)
- Custom branding (white-label)
```

**Deployment**: Standalone FastAPI service (isolated, customer_id scoped)

---

## Decision Matrix: Which Architecture for Which Domain?

| Domain | Use Skills Executor IF... | Use Code Factory IF... |
|--------|--------------------------|------------------------|
| **ECM** | Internal ops team (< 50 users) | Selling to shipping companies (> 1K users) |
| **FinCrime** | Internal analysts (< 20 users) | Compliance software for banks (> 500 users) |
| **Fraud Guardian** | Internal risk team (< 10 users) | Selling rule simulator as SaaS (> 100 users) |
| **Wealth** | NEVER (too high scale) | ALWAYS (retail investors, > 10K users) |

### Heuristics

**Use Skills Executor when**:
- ✅ Internal team (< 100 users)
- ✅ Rapid iteration needed (add skills daily)
- ✅ Team-scoped data (shared queue, collaborative)
- ✅ Low cost priority (shared runtime)
- ✅ NOT customer-facing

**Use Code Factory to generate standalone product when**:
- ✅ Customer-facing (> 1K users)
- ✅ Blast radius isolation required (critical domain)
- ✅ Independent scaling needed (traffic spikes)
- ✅ Compliance/audit requirements (isolated service)
- ✅ Monetization plan (SaaS product)

---

## How They Work Together

### Code Factory BUILDS the Skills Executor

The Skills Executor platform itself is CODE-GENERATED by the Code Factory:

```
spec.md: "Build a multi-domain skills executor with Pydantic AI"
         ↓
Code Factory Agent generates:
- packages/executor/skill_executor.py
- packages/registry/domain_registry.py
- channels/slack/bot.py
- channels/whatsapp/webhook.py
- .aspora/risk-policy.json (critical tier for executor core)
```

**Workflow**:
1. PM writes executor spec
2. Coding Agent generates SkillExecutor class
3. Risk Policy Gate: executor core = CRITICAL tier (requires human review)
4. Code Review Agent checks for context injection bugs
5. Remediation Agent fixes missing validation
6. GitHub Actions deploys executor platform

**Why This Works**:
- ✅ **Dogfooding** — Code Factory maintains the executor it builds
- ✅ **Consistency** — Same risk policies for executor and products
- ✅ **Audit Trail** — Every executor change has SHA-discipline
- ✅ **Quality** — Review agents catch security bugs in executor

---

## Hackathon Strategy: Build Both

### What to Build in 36 Hours

**Hours 0-18**: Skills Executor Platform (Core Demo)
- Build SkillExecutor with Pydantic AI
- Onboard ECM, FinCrime, Fraud Guardian as skills
- Multi-agent workflow (field → manager → analyst)
- Slack integration with context injection

**Hours 18-24**: Code Factory Prototype (Differentiator)
- Build Coding Agent (spec.md → FastAPI service)
- Risk Policy Gate (tier-based merge rules)
- Code Review Agent wrapper (call Greptile API)
- Demo: Generate Wealth portfolio checker in 10 minutes LIVE

**Hours 24-30**: Integration Demo (The "Wow")
- Show Code Factory generating a NEW skill for Skills Executor
- PM writes spec → Agent generates skill → Auto-deploys to executor
- Field agent immediately uses new skill in Slack
- "From spec to production in 5 minutes — NO human coding"

**Hours 30-36**: Polish + Rehearsal

---

## Demo Script: Showing Both Architectures

**Act 1 (60s): Skills Executor for Operations**
```
[Slack: Sarah (ECM field agent)]
Sarah: "show my tickets"
Bot: 📋 Your Tickets (5 pending)...

Sarah: "escalate ticket 1234"
Bot: 🚀 Escalated to Manager

[Switch to Raj (FinCrime analyst)]
Raj: "show alerts"
Bot: 🚨 FinCrime Queue (12 alerts)...

"Three domains. Shared platform. Context injection handles multi-tenancy."
```

**Act 2 (90s): Code Factory Generating Products**
```
[Show Code Factory dashboard]
PM: "Let's add a Wealth domain for retail investors"

[Type spec.md]:
```markdown
# Wealth Portfolio Checker
- GET /portfolio/{user_id} — Show holdings with P&L
- Risk: Kelly Criterion position sizing
- Multi-currency (INR, USD, AED)
```

[Click "Generate"]

[Code Factory runs]:
1. ✅ Coding Agent generates FastAPI service (15s)
2. ✅ Risk Policy Gate: Tier = HIGH (contains finance logic)
3. ✅ Code Review Agent: 0 critical issues
4. ✅ Remediation Agent: Fixed 2 minor issues
5. ✅ Deployed to wealth.aspora.io (30s)

[Test generated API]:
```bash
curl https://wealth.aspora.io/portfolio/priya
```

Response:
```json
{
  "portfolio_value_inr": 850000,
  "holdings": [
    {"symbol": "RELIANCE.NS", "value": 189950, "pnl_pct": 3.2}
  ],
  "risk_status": "green"
}
```

"From spec to deployed API in 90 seconds. Zero human coding."
```

**Act 3 (30s): The Integration Magic**
```
[Show Code Factory generating ECM skill]
PM writes skill spec → Agent generates field/my-tickets.md
→ Auto-commits to domains/ecm/skills/
→ Skills Executor hot-reloads registry
→ Sarah in Slack immediately uses new skill

"Code Factory writes the skills. Executor runs them. Agents all the way down."
```

---

## Engineering Comparison

| Aspect | Skills Executor | Code Factory |
|--------|-----------------|--------------|
| **Latency** | < 1s (real-time skill execution) | N/A (build-time tool) |
| **Scalability** | Moderate (shared runtime, noisy neighbor) | High (generates isolated services) |
| **Blast Radius** | HIGH (executor crash = all domains down) | LOW (only dev tooling) |
| **Cost** | $42K/year (shared OpenRouter) | Negligible (only runs during builds) |
| **Observability** | Complex (multi-domain traces) | Simple (GitHub Actions logs) |
| **User Impact** | CRITICAL (production runtime) | LOW (dev tooling) |
| **When to Scale** | When > 100 users per domain | Never (stays build-time tool) |

---

## Revised Architectural Decision

### DEC-014: Skills Executor for Internal Ops, Code Factory for Customer Products

**Chose**: Dual architecture (Skills Executor + Code Factory)
**Over**: Single architecture (either executor-only OR code-gen-only)

**Why**:
1. **Skills Executor** optimized for internal teams (< 100 users, rapid iteration, team-scoped data)
2. **Code Factory** optimized for customer products (> 1K users, blast radius isolation, monetization)
3. They are COMPLEMENTARY — Code Factory maintains the Executor platform
4. Clear separation of concerns (build-time vs run-time)

**Constraints**:
- Skills Executor MUST remain internal-only (< 100 users per domain threshold)
- If domain exceeds 100 users, Code Factory generates standalone product version
- Code Factory outputs MUST pass risk policy gates before merge
- Both architectures share same observability stack (OpenTelemetry, Prometheus)

**Migration Path**:
```
ECM starts as skill on executor (10 users)
→ Grows to 50 users (still okay on executor)
→ Exceeds 100 users (trigger graduation)
→ Code Factory generates ecm-product/ (FastAPI service)
→ Strangler Fig migration over 6 months
→ ECM product sold as SaaS to shipping companies
```

---

## Summary: Answer to Your Question

**Q: How does Code Factory differ from Skills Executor (OpenClaw-style) for ECM/FinCrime?**

**A**: They serve DIFFERENT purposes:

1. **Skills Executor** = Production runtime for internal operations
   → ECM field agents, FinCrime analysts use it daily
   → Real-time skill execution with context injection
   → Shared platform across domains

2. **Code Factory** = Build-time coding agent for generating products
   → Generates standalone FastAPI services (Wealth API, eventually ECM SaaS)
   → Risk-aware CI/CD with automated review
   → NOT in production critical path

**For ECM/FinCrime specifically**:
- **Phase 1 (Now)**: Use Skills Executor for internal ops teams (< 50 users)
- **Phase 2 (When > 100 users)**: Code Factory generates standalone product
- **Phase 3 (SaaS)**: Sell ECM/FinCrime products to external customers

**The Brilliant Symbiosis**:
- Code Factory BUILDS the Skills Executor platform
- Skills Executor RUNS the skills for internal teams
- Code Factory GENERATES customer-facing products
- Both share same risk policies, review agents, observability

**For Hackathon**:
- Hours 0-18: Build Skills Executor (ECM, FinCrime, Fraud)
- Hours 18-24: Build Code Factory prototype
- Hours 24-30: DEMO Code Factory generating new skill → Executor immediately runs it
- "Agents writing agents. From spec to production in 5 minutes."
