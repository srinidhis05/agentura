# Aspora Platform — Current Status

> **Last Updated**: 2026-02-16
> **Phase**: Research & Planning Complete ✅

---

## Platform Vision

**Aspora** is a skill marketplace for multi-domain agentic applications. Teams independently build, test, deploy, and monetize skills across:
- **Wealth Copilot** (cross-border finance)
- **Fraud Guardian** (transaction risk)
- **ECM Dev Agent** (codebase intelligence)
- **Retention** (customer lifecycle)
- **Support** (automated customer service)
- **Operations** (internal workflows)

---

## Documentation Complete

### ✅ Platform Design
- **ASPORA_PLATFORM_DESIGN.md** — Three-layer architecture (Gateway + Agents + Skills Runtime)
- **ASPORA_PLATFORM_SDK.md** — Developer SDK, skill registry, OpenRouter integration, observability
- **IMPLEMENTATION_PLAN.md** — Phase-by-phase buildout with primitives
- **DECISIONS.md** — 10 architectural decisions preserved for future reference

### ✅ Key Technical Decisions
1. **Pydantic AI** for type-safe agents (NOT OpenClaw — security concerns)
2. **Custom communication gateway** using official SDKs (Slack Bolt, Meta WhatsApp)
3. **OpenRouter** for model gateway (auto-fallback, cost optimization)
4. **Skill marketplace model** (like Shopify apps)
5. **Multi-language support** (TypeScript, Python, Go)
6. **PostgreSQL skill registry** with S3/R2 code storage
7. **Firecracker VMs** for secure skill sandboxing
8. **Three-tier observability** (Platform → Domain → Skill)
9. **Canary deployments** with auto-rollback
10. **Feedback loop as moat** (user corrections → auto test generation)

---

## Current Codebase State

### TypeScript (Next.js 14 + Prisma)
```
packages/
├── core/domain/types.ts   # Domain types (Money, Goal, Risk)
├── core/scoring/          # Risk scoring engine
└── skills/                # Existing skills (safety, wealth)

apps/
└── web/                   # Next.js frontend
```

### Python (Pydantic AI)
```
agents/
└── core/
    ├── types.py          # Domain types (Currency, GoalType, RiskTolerance, Money)
    ├── __init__.py       # Exports WealthCopilotAgent, Skill, SkillRegistry
    ├── agent.py          # NOT YET CREATED
    └── skill.py          # NOT YET CREATED
```

**Status**: Domain types exist, but agent implementation is stubbed.

---

## Platform Architecture Stack

```
┌─────────────────────────────────────────────────────┐
│   DEVELOPER SDK LAYER                               │
│   • Aspora CLI (create, test, deploy)              │
│   • Skill Studio (Web IDE)                         │
│   • Dev Portal (docs, analytics, marketplace)      │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│   SKILL REGISTRY & DISCOVERY                        │
│   • PostgreSQL (metadata, triggers, permissions)    │
│   • S3/R2 (skill code storage)                      │
│   • Semantic search for LLM discovery               │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│   EXECUTION RUNTIME                                 │
│   • Firecracker VMs (sandboxed execution)          │
│   • Redis skill cache (hot skills, fast startup)   │
│   • Tool Library (Read, Write, Bash, WebFetch, etc)│
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│   MODEL GATEWAY (OpenRouter)                        │
│   • Auto model selection (Haiku/Sonnet/Opus)       │
│   • Fallback across providers                      │
│   • Cost tracking + budget enforcement              │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│   OBSERVABILITY & MONITORING                        │
│   • Opik (tracing)                                  │
│   • Langfuse (conversation logging + feedback)     │
│   • Prometheus (metrics) + Grafana (dashboards)    │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: MVP Platform (2 weeks)

**Week 1: Core Platform**
- [ ] Skill registry (PostgreSQL schema)
- [ ] Aspora CLI (`aspora create`, `aspora test`, `aspora deploy`)
- [ ] OpenRouter gateway (model selection + fallback)
- [ ] Basic observability (Prometheus metrics)

**Week 2: First Domain (Wealth Copilot)**
- [ ] Migrate existing Wealth Copilot to platform
- [ ] 3 skills: `create-goal`, `suggest-allocation`, `fx-timing`
- [ ] DeepEval test suite
- [ ] Grafana dashboard

### Phase 2: Multi-Domain (2 weeks)

**Week 3: Onboard Fraud + ECM**
- [ ] Fraud team deploys 3 skills via CLI
- [ ] ECM team deploys 2 skills
- [ ] Cross-domain testing

**Week 4: Advanced Features**
- [ ] Canary deployments
- [ ] Cost budgets + alerts
- [ ] Skill versioning + rollback

---

## Parallel Workstreams (Teams Work Independently)

| Team | Week 1-2 | Week 3-4 | Blocker? |
|------|----------|----------|----------|
| **Platform Team** | Build registry, CLI, gateway | Polish monitoring, docs | None |
| **Wealth Team** | Continue building wealth skills | Migrate to platform | None |
| **Fraud Team** | Build fraud skills in sandbox | Onboard to platform | Wait for Week 3 |
| **ECM Team** | Build ECM skills locally | Onboard to platform | Wait for Week 3 |

**NO BLOCKERS** — teams build skills independently, platform team builds infrastructure in parallel.

---

## Developer Experience Preview

### Creating a Skill
```bash
# Install CLI
npm install -g @aspora/cli

# Create new skill (auto-scaffolds SKILL.md, DECISIONS.md, GUARDRAILS.md, code/, tests/)
aspora create skill fraud/block-transaction

# Test locally
aspora test fraud/block-transaction

# Deploy to staging
aspora deploy --env staging fraud/block-transaction

# Monitor
aspora logs fraud/block-transaction --follow
aspora metrics fraud/block-transaction --last 24h
```

### Skill Configuration (aspora.config.yaml)
```yaml
skill:
  name: block-transaction
  domain: fraud
  version: 1.0.0

runtime:
  language: typescript
  timeout: 30s
  memory: 512MB

model:
  primary: claude-sonnet-4-5
  fallback: gpt-4o-mini
  cost_budget:
    max_per_execution: 0.10
    monthly_limit: 1000.00

triggers:
  - type: message
    patterns: ["fraud", "suspicious transaction"]
  - type: cron
    schedule: "0 * * * *"
```

### TypeScript Handler
```typescript
export const handler: AsporaSkillHandler = async (context) => {
  const fraudScore = await context.apis.trm.checkTransaction({
    transactionId: context.input.metadata.transactionId,
  });

  if (fraudScore > 0.8) {
    return {
      success: true,
      message: '🚫 Transaction blocked',
      data: { fraudScore, action: 'blocked' },
      confidence: 0.95,
    };
  }

  return {
    success: true,
    message: '✅ Transaction approved',
    data: { fraudScore, action: 'approved' },
    confidence: 0.85,
  };
};
```

---

## Competitive Moat

After 6 months of production:
- **50+ skills** across 6 domains
- **10,000+ test cases** (from user corrections → auto test generation)
- **Cost optimization data** (which models for which tasks)
- **Production-grade observability** (Grafana dashboards, PagerDuty integrations)

New competitor would need to rebuild ALL of this.

---

## Next Steps

### Option A: Immediate Implementation (Start Phase 1)
1. Create PostgreSQL schema for skill registry
2. Build Aspora CLI (TypeScript with Commander.js)
3. Implement OpenRouter gateway
4. Set up Prometheus + Grafana

### Option B: Validate with Stakeholders
1. Review ASPORA_PLATFORM_SDK.md with team
2. Prioritize domains (Wealth first? Fraud first?)
3. Confirm budget for OpenRouter ($1000-5000/month?)
4. Align on 2-week sprint commitment

### Option C: Build First Primitive (< 2 hours)
1. **Primitive 1.1**: Skill registry schema (PostgreSQL)
2. **Test**: `aspora create skill test/hello-world` → generates scaffold
3. **Demo**: Show team scaffolded skill structure

---

## Questions for Stakeholder Review

1. **Priority**: Which domain should onboard first? (Wealth vs Fraud vs ECM)
2. **Budget**: What's the monthly LLM cost budget? ($1k, $5k, $10k?)
3. **Team Size**: How many developers per domain team?
4. **Timeline**: 2-week sprint commitment feasible?
5. **Security**: Firecracker VMs OK, or prefer Docker for MVP?

---

**Status**: ✅ Planning complete. Ready for stakeholder review or immediate implementation.
