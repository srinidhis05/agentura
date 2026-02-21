# Engineering Comparison: Traditional vs Platform Architecture

**Question**: Should Wealth be a separate product with its own frontend/backend, or a domain on the Aspora platform?

**Answer**: It depends on your business model and stage. Both are valid. Here's the honest engineering trade-offs.

---

## Two Architectures

### Architecture A: Traditional Separate Product

```
┌─────────────────────────────────────────┐
│ Wealth Product (Standalone)            │
│                                         │
│  ┌──────────────┐    ┌──────────────┐ │
│  │ React/Next.js│    │ Python/FastAPI│ │
│  │   Frontend   │───▶│    Backend    │ │
│  │              │    │               │ │
│  │ - Portfolio  │    │ - Portfolio   │ │
│  │ - Goals      │    │   Service     │ │
│  │ - Trades     │    │ - Trading     │ │
│  │ - Analytics  │    │   Engine      │ │
│  └──────────────┘    │ - Risk Mgmt   │ │
│                       │ - Broker APIs │ │
│                       └───────┬───────┘ │
│                               │         │
│                       ┌───────▼───────┐ │
│                       │   PostgreSQL  │ │
│                       │   TimescaleDB │ │
│                       └───────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ECM/FinCrime Platform (Separate)        │
│                                         │
│  ┌──────────────┐    ┌──────────────┐ │
│  │ Operations   │    │   Aspora     │ │
│  │   Dashboard  │───▶│   Platform   │ │
│  └──────────────┘    └──────────────┘ │
└─────────────────────────────────────────┘
```

### Architecture B: Platform-First Multi-Domain

```
┌───────────────────────────────────────────────────────────┐
│              Aspora Multi-Domain Platform                 │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         Unified Execution Layer                      │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │ │
│  │  │ OpenRouter   │  │ SkillExecutor│  │  Context  │ │ │
│  │  │   Gateway    │─▶│   + RBAC     │─▶│ Injection │ │ │
│  │  └──────────────┘  └──────────────┘  └───────────┘ │ │
│  └─────────────────────────────────────────────────────┘ │
│                           │                               │
│         ┌─────────────────┼─────────────────┐            │
│         │                 │                 │            │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐     │
│  │ECM Domain   │  │FinCrime     │  │Wealth Domain│     │
│  │(Team-scoped)│  │(Team-scoped)│  │(User-scoped)│     │
│  │             │  │             │  │             │     │
│  │ 9 skills    │  │ 1 skill     │  │ 3 skills    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         Domain-Specific Services (Optional)          │ │
│  │  - Portfolio Service (wealth)                        │ │
│  │  - Broker Integration Gateway (wealth)               │ │
│  │  - TRM Rules Engine (fincrime)                       │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         Unified Data Layer                           │ │
│  │  PostgreSQL (multi-tenant, row-level security)       │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘

     Multiple UIs connect to same platform:
     - Slack (operations teams)
     - WhatsApp (retail wealth users)
     - Web Dashboard (internal tools)
```

---

## Engineering Comparison Matrix

| Dimension | Traditional (Separate Products) | Platform-First (Multi-Domain) | Winner |
|-----------|--------------------------------|------------------------------|--------|
| **Initial Build Time** | 3-4 months per product | 1-2 months for platform + domains | **Platform** (shared infra) |
| **Time to Add Domain** | 3-4 months (new product) | 1-2 weeks (new domain config) | **Platform** (10x faster) |
| **Scalability: Vertical** | Scale entire product stack | Scale per-domain or per-skill | **Platform** (granular) |
| **Scalability: Horizontal** | Independent scaling per product | Shared platform, domain isolation | **Tie** (different patterns) |
| **Blast Radius** | Product-level (wealth fails, ECM unaffected) | Platform-level (executor fails, all domains down) | **Traditional** (isolation) |
| **Observability: Tracing** | Per-product APM (separate Datadog) | Unified observability, cross-domain traces | **Platform** (holistic view) |
| **Observability: Debugging** | Simpler (less abstraction) | Complex (executor + domain + skill layers) | **Traditional** (simplicity) |
| **Reliability: SLA** | Independent SLAs per product | Shared platform SLA, domain-level SLOs | **Traditional** (independence) |
| **Reliability: Failure Modes** | Database, API, UI failures per product | Executor failure, skill load failure, context injection failure | **Traditional** (fewer shared components) |
| **Cost: Infrastructure** | N × (compute + DB + monitoring) | 1 × platform + domain-specific services | **Platform** (shared overhead) |
| **Cost: Development** | N teams (frontend + backend each) | 1 platform team + domain skill writers | **Platform** (smaller team) |
| **Developer Velocity** | Faster for isolated changes | Slower for platform changes, faster for skills | **Tie** (depends on change type) |
| **Team Structure** | Product teams (full stack per domain) | Platform team + domain specialists | **Traditional** (autonomy) |
| **Compliance: Audit** | Per-product audit trails | Unified audit log, cross-domain analysis | **Platform** (regulatory efficiency) |
| **Security: Attack Surface** | N attack surfaces (N products) | 1 platform attack surface + domain boundaries | **Platform** (smaller surface) |
| **Vendor Lock-In** | None (standard tech stack) | Locked to Aspora platform abstractions | **Traditional** (portability) |
| **Innovation Speed** | Slow (rebuild infra per product) | Fast (reuse platform for new domains) | **Platform** (leverage existing) |
| **Feature Reuse** | Copy-paste or shared libraries | Native cross-domain composition | **Platform** (built-in) |
| **Testing Complexity** | Simpler (isolated product tests) | Complex (platform + domain + integration tests) | **Traditional** (test pyramid) |
| **Deployment Complexity** | N independent deployments | 1 platform + domain configs (backward compat required) | **Traditional** (simpler rollback) |
| **Data Consistency** | Per-product consistency | Cross-domain consistency challenges | **Traditional** (bounded context) |
| **User Experience: Single Domain** | Polished, domain-optimized | Shared UI patterns, may lack specificity | **Traditional** (UX depth) |
| **User Experience: Cross-Domain** | Multiple logins, no integration | Single login, cross-domain workflows | **Platform** (unified experience) |

---

## Deep Dive: Scalability

### Traditional Approach

```yaml
# Docker Compose / Kubernetes deployment
services:
  wealth-frontend:
    image: wealth-ui:latest
    replicas: 3
    resources:
      cpu: 0.5
      memory: 512Mi

  wealth-backend:
    image: wealth-api:latest
    replicas: 5
    resources:
      cpu: 1
      memory: 2Gi
    autoscaling:
      min: 5
      max: 50
      target_cpu: 70%

  wealth-db:
    image: postgres:15
    replicas: 1 (primary) + 2 (read replicas)
    resources:
      cpu: 4
      memory: 16Gi

  wealth-broker-gateway:
    image: broker-gateway:latest
    replicas: 3
    resources:
      cpu: 2
      memory: 4Gi

# Separate deployment for ECM
services:
  ecm-frontend: [...]
  ecm-backend: [...]
  ecm-db: [...]
```

**Scaling Characteristics**:
- ✅ **Independent scaling**: Wealth traffic spike doesn't affect ECM
- ✅ **Clear capacity planning**: Each product has known resource profile
- ✅ **Horizontal scaling**: Just add replicas per service
- ❌ **Resource overhead**: Each product has minimum 3 services (UI, API, DB)
- ❌ **Cold start**: New domain = spin up entire stack
- ❌ **Wasted capacity**: ECM backend might be idle while Wealth is overloaded

**Bottlenecks**:
- Database per product (need read replicas, sharding)
- Broker API rate limits (shared across all users)
- Frontend bundle size (grows with features)

### Platform Approach

```yaml
# Platform deployment
services:
  aspora-executor:
    image: aspora-platform:latest
    replicas: 10
    resources:
      cpu: 2
      memory: 4Gi
    autoscaling:
      min: 10
      max: 100
      target_cpu: 70%
    env:
      - OPENROUTER_KEY=xxx
      - DOMAIN_CONFIGS=/domains/*/aspora.config.yaml

  aspora-db:
    image: postgres:15
    replicas: 1 (primary) + 3 (read replicas)
    resources:
      cpu: 8
      memory: 32Gi
    # Row-level security for multi-tenancy
    config:
      - row_level_security=on

  # Domain-specific services (optional, only if needed)
  wealth-portfolio-service:
    image: portfolio-service:latest
    replicas: 3
    resources:
      cpu: 1
      memory: 2Gi
    # Called by wealth skills via HTTP

  wealth-broker-gateway:
    image: broker-gateway:latest
    replicas: 3
    resources:
      cpu: 2
      memory: 4Gi

  fincrime-rules-engine:
    image: fincrime-engine:latest
    replicas: 5
    resources:
      cpu: 2
      memory: 4Gi
```

**Scaling Characteristics**:
- ✅ **Elastic scaling**: Executor scales for ALL domains (efficient resource use)
- ✅ **Fast domain onboarding**: New domain = config file, no new infra
- ✅ **Skill-level routing**: Can route expensive skills to larger executor instances
- ❌ **Noisy neighbor**: Wealth traffic spike affects ECM (shared executor pool)
- ❌ **Complex capacity planning**: Mixed workload makes resource prediction harder
- ❌ **Platform as bottleneck**: Executor failure impacts all domains

**Bottlenecks**:
- SkillExecutor throughput (mitigate: autoscale executors)
- OpenRouter rate limits (mitigate: model-level queueing)
- Shared database (mitigate: read replicas, per-domain schemas)
- Skill loading time (mitigate: lazy loading, skill caching)

**Scalability Fix for Noisy Neighbor**:

```yaml
# Dedicated executor pools per domain scope
services:
  aspora-executor-ops:  # For ECM, FinCrime (team-scoped)
    image: aspora-platform:latest
    replicas: 5
    env:
      - DOMAIN_FILTER=ecm,fincrime  # Only load these domains
    resources:
      cpu: 2
      memory: 4Gi

  aspora-executor-wealth:  # For Wealth (user-scoped)
    image: aspora-platform:latest
    replicas: 10
    env:
      - DOMAIN_FILTER=wealth
    resources:
      cpu: 1
      memory: 2Gi
```

This gives you independent scaling like Traditional, but with shared platform code.

---

## Deep Dive: Monitorability

### Traditional Approach

```yaml
# Datadog APM for Wealth Product
datadog:
  service: wealth-backend
  env: production
  metrics:
    - wealth.api.request.latency
    - wealth.portfolio.load.duration
    - wealth.broker.order.success_rate
    - wealth.db.query.duration
  traces:
    - /api/portfolio
    - /api/trade
    - /api/goals
  logs:
    - INFO: User X viewed portfolio
    - ERROR: Broker API timeout
    - WARN: Daily loss limit triggered

# Separate Datadog instance for ECM
datadog:
  service: ecm-backend
  metrics:
    - ecm.ticket.assignment.duration
    - ecm.runbook.execution.success_rate
  traces: [...]
  logs: [...]
```

**Observability Characteristics**:
- ✅ **Simpler traces**: Request → API → Database → Response
- ✅ **Clear ownership**: Wealth team owns wealth-backend dashboards
- ✅ **Easier debugging**: Fewer layers, direct code path
- ❌ **No cross-product correlation**: Can't trace "user verified ECM ticket, then checked portfolio"
- ❌ **Duplicate monitoring setup**: Each product needs dashboards, alerts, runbooks
- ❌ **Fragmented costs**: N × Datadog/Prometheus instances

**Sample Dashboard**:
```
WEALTH BACKEND DASHBOARD
========================
Request Rate:        1,200 req/min
P95 Latency:         250ms
Error Rate:          0.5%
Database Conns:      45/100
Broker API Errors:   2/min

Top Endpoints:
1. GET /api/portfolio      (800 req/min, 150ms p95)
2. POST /api/trade         (300 req/min, 400ms p95)
3. GET /api/goals          (100 req/min, 100ms p95)
```

### Platform Approach

```yaml
# Unified Datadog APM for Aspora Platform
datadog:
  service: aspora-platform
  env: production
  metrics:
    - aspora.skill.execution.latency (tagged by: domain, skill_name, model)
    - aspora.skill.cost (tagged by: domain, user_id, model)
    - aspora.executor.queue.depth
    - aspora.openrouter.request.duration
    - aspora.context.injection.errors
  traces:
    - User Request → SkillExecutor → Domain Loader → OpenRouter → Skill Execution → Response
  logs:
    - INFO: Skill wealth/portfolio-check executed for user=priya@aspora.com cost=$0.02
    - ERROR: Skill ecm/field/my-tickets failed: missing context team_id
    - WARN: OpenRouter rate limit hit for model=anthropic/claude-sonnet-4.5

# Domain-specific service monitoring
datadog:
  service: portfolio-service
  metrics:
    - portfolio.calculation.duration
    - portfolio.broker.api.errors
```

**Observability Characteristics**:
- ✅ **Unified view**: See all domains in one dashboard
- ✅ **Cross-domain traces**: Can trace "ECM ticket → FinCrime alert → Wealth risk check"
- ✅ **Cost attribution**: Track OpenRouter spend by domain, user, skill
- ❌ **Complex traces**: More hops (executor → loader → skill → service)
- ❌ **Tag explosion**: High cardinality (domain × skill × user × model)
- ❌ **Harder debugging**: Abstractions hide direct code path

**Sample Dashboard**:
```
ASPORA PLATFORM DASHBOARD
=========================
Total Skill Executions:  5,400/min
  - ECM:       2,000/min
  - FinCrime:    800/min
  - Wealth:    2,600/min

P95 Latency by Domain:
  - ECM:        180ms (mostly Haiku, fast)
  - FinCrime:   850ms (Sonnet, complex reasoning)
  - Wealth:     120ms (Haiku, simple queries)

OpenRouter Costs (hourly):
  - ECM:       $2.40 (Haiku heavy)
  - FinCrime:  $8.50 (Sonnet heavy)
  - Wealth:    $1.20 (Haiku, high volume)

Errors (last hour):
  - Missing context: 12 (fix: update skill config)
  - OpenRouter timeout: 3 (retry succeeded)
  - Skill load failure: 1 (fincrime/investigate-alert.md syntax error)
```

**Debugging Comparison**:

| Scenario | Traditional | Platform |
|----------|-------------|----------|
| "Portfolio load is slow" | Check wealth-backend logs → DB query → Done | Check executor logs → Find skill execution → Check if OpenRouter slow or portfolio-service slow → Trace shows call to portfolio-service → Check portfolio-service logs |
| "User reported error" | Check user_id in wealth logs → Find request → See error | Check user_id across ALL domains → Find which skill failed → Check executor + domain logs |
| "High latency spike" | Check wealth-backend metrics → Frontend or backend? | Check executor metrics → Which domain? → Which skill? → Which model? → More drill-down |

**Verdict**: Traditional is **easier to debug** for single-domain issues. Platform is **more powerful** for cross-domain analysis but requires better instrumentation hygiene.

---

## Deep Dive: Reliability

### Traditional Approach

**Failure Modes**:

```
Wealth Product Failure Scenarios:
1. Frontend crash          → Users can't access UI, backend unaffected
2. Backend crash           → API down, frontend shows errors
3. Database failover       → Brief downtime (30s), read replicas continue
4. Broker API outage       → Trading disabled, portfolio viewing works
5. Cache (Redis) failure   → Degraded performance, fallback to DB

Impact: ONLY wealth users affected. ECM/FinCrime continue normally.
```

**SLA Structure**:
```yaml
wealth_product:
  sla: 99.9%  # ~43 minutes downtime/month
  components:
    frontend: 99.95%
    backend: 99.9%
    database: 99.99% (managed Postgres)
    broker_gateway: 99.5% (external dependency)

ecm_product:
  sla: 99.9%
  components: [independent]
```

**Reliability Tactics**:
- Health checks per service
- Circuit breakers for broker API
- Database connection pooling
- Graceful degradation (show cached portfolio if broker API down)
- Independent deployments (wealth can deploy without affecting ECM)

### Platform Approach

**Failure Modes**:

```
Platform Failure Scenarios:
1. SkillExecutor crash     → ALL domains down until restart (BLAST RADIUS: 100%)
2. Database failover       → All domains briefly unavailable
3. OpenRouter outage       → No skill can execute across any domain
4. Domain config load fail → That domain disabled, others continue
5. Skill syntax error      → That skill fails, other skills in domain continue
6. Context injection bug   → Domain fails permission checks, halts execution
7. Portfolio service crash → Only wealth skills affected, ECM/FinCrime OK

Impact: Executor and DB failures affect ALL domains (shared fate).
```

**SLA Structure**:
```yaml
aspora_platform:
  sla: 99.9%  # Platform-level SLA
  components:
    executor: 99.95% (critical path)
    database: 99.99%
    openrouter: 99.5% (external, out of our control)

  slos_per_domain:  # Service-level objectives (not guarantees)
    ecm:
      p95_latency: < 200ms
      error_rate: < 0.5%
    fincrime:
      p95_latency: < 1000ms (Sonnet is slow)
      error_rate: < 0.1% (compliance-critical)
    wealth:
      p95_latency: < 150ms
      error_rate: < 1%
```

**Reliability Tactics**:
- Multi-AZ executor deployment (10+ replicas)
- Database read replicas
- OpenRouter fallback to direct Anthropic API
- Skill-level circuit breakers
- Domain isolation via separate executor pools (see Scalability section)
- Canary deployments with auto-rollback
- Graceful degradation: If OpenRouter down, return cached results + warning

**Blast Radius Mitigation**:

```python
# Executor with domain isolation
class ResilientSkillExecutor:
    def __init__(self):
        self.executors = {
            'ops': SkillExecutor(domains=['ecm', 'fincrime']),  # Separate pool
            'wealth': SkillExecutor(domains=['wealth'])         # Separate pool
        }

    async def execute(self, skill_id: str, context: dict):
        domain = skill_id.split('/')[0]
        pool = 'wealth' if domain == 'wealth' else 'ops'

        try:
            return await self.executors[pool].execute(skill_id, context)
        except Exception as e:
            # Log failure, return degraded response
            logger.error(f"Skill {skill_id} failed in pool {pool}: {e}")
            return {
                "error": "Service temporarily unavailable",
                "fallback": self._get_cached_result(skill_id, context)
            }
```

**Verdict**: Traditional has **better blast radius isolation** (product-level). Platform has **shared fate risk** but can be mitigated with domain pools and circuit breakers.

---

## Cost Analysis (Annual, 10K Users)

### Traditional Approach

```
Infrastructure Costs (AWS):
  Wealth Frontend (CloudFront + S3):           $500/mo
  Wealth Backend (ECS Fargate, 5 tasks):     $1,200/mo
  Wealth Database (RDS Postgres, db.m5.large): $800/mo
  Wealth Redis (ElastiCache):                  $200/mo
  Broker Gateway (ECS Fargate):                $600/mo

  ECM Frontend:                                 $500/mo
  ECM Backend:                                $1,200/mo
  ECM Database:                                 $800/mo

  FinCrime Backend:                           $1,500/mo
  FinCrime Database:                          $1,000/mo

  TOTAL INFRASTRUCTURE: $8,300/mo = $99,600/year

Observability (Datadog):
  3 products × $2,000/mo:                     $6,000/mo = $72,000/year

AI/LLM Costs (if used):
  Direct Anthropic API:                      ~$5,000/mo = $60,000/year
  (No OpenRouter, pay per API call)

Development Team:
  3 product teams:
    - Wealth: 2 frontend + 2 backend + 1 DevOps = 5 people
    - ECM: 2 frontend + 2 backend (shared DevOps) = 4 people
    - FinCrime: 1 frontend + 2 backend (shared DevOps) = 3 people
  Total: 12 people × $120K/year = $1,440,000/year

ANNUAL TOTAL: $1,671,600
```

### Platform Approach

```
Infrastructure Costs (AWS):
  Aspora Executor (ECS Fargate, 10 tasks):   $2,400/mo
  Shared Database (RDS, db.m5.2xlarge):      $1,600/mo
  Shared Redis (ElastiCache):                  $300/mo

  Domain-specific services:
    Portfolio Service (ECS, 3 tasks):          $720/mo
    Broker Gateway (ECS, 3 tasks):             $720/mo
    FinCrime Rules Engine (ECS, 5 tasks):    $1,200/mo

  TOTAL INFRASTRUCTURE: $6,940/mo = $83,280/year

Observability (Datadog):
  1 unified platform:                        $3,000/mo = $36,000/year

AI/LLM Costs (OpenRouter):
  OpenRouter with smart routing:            ~$3,500/mo = $42,000/year
  (15% markup over direct API, but better uptime and fallbacks)

Development Team:
  1 platform team:
    - 2 platform engineers (executor, infra) = 2 people
    - 1 DevOps engineer = 1 person
  3 domain teams (skills-focused):
    - Wealth: 1 frontend + 1 skill developer = 2 people
    - ECM: 1 skill developer (shared frontend) = 1 person
    - FinCrime: 1 skill developer (shared frontend) = 1 person
  Total: 7 people × $120K/year = $840,000/year

ANNUAL TOTAL: $1,001,280
```

### Cost Comparison

| Category | Traditional | Platform | Savings |
|----------|-------------|----------|---------|
| Infrastructure | $99,600 | $83,280 | **$16,320 (16%)** |
| Observability | $72,000 | $36,000 | **$36,000 (50%)** |
| LLM Costs | $60,000 | $42,000 | **$18,000 (30%)** |
| Team Costs | $1,440,000 | $840,000 | **$600,000 (42%)** |
| **TOTAL** | **$1,671,600** | **$1,001,280** | **$670,320 (40%)** |

**Biggest Savings**: Team costs (fewer full-stack engineers, more skill specialists).

---

## When to Choose Each Approach

### Choose Traditional (Separate Products) If:

✅ **You're building 1-2 products max** — Platform overhead not justified
✅ **Each product has dedicated team** — Full-stack autonomy matters
✅ **Blast radius isolation is critical** — Wealth failure CANNOT affect compliance systems
✅ **Regulatory requirements mandate separation** — FinCrime data must be in isolated environment
✅ **You need product-specific tech stacks** — Wealth uses Go, ECM uses Java, FinCrime uses Python
✅ **Team prefers simplicity over reuse** — Less abstraction, faster debugging
✅ **You're a scale-up (Series B+) with established products** — Microservices architecture makes sense

**Example**: Banking incumbent with separate divisions. Wealth management is Div A, FinCrime is Div B. They don't talk. Separation is a feature, not a bug.

### Choose Platform (Multi-Domain) If:

✅ **You're building 3+ domains** — Shared platform pays for itself
✅ **Domains share patterns** — Skills-based approach works across ECM, FinCrime, Wealth
✅ **Cross-domain workflows exist** — "Wealth user flags suspicious deposit → FinCrime investigates"
✅ **Small team (<10 people)** — Can't afford 3 product teams
✅ **Fast iteration is priority** — Add new domain in 1-2 weeks vs 3-4 months
✅ **Cost efficiency matters** — Startup/early-stage, need to minimize burn
✅ **Unified user experience** — Same login, same channels (Slack/WhatsApp), cross-domain context
✅ **You're building a marketplace** — Want third parties to contribute skills

**Example**: Early-stage startup (Seed to Series A) building multi-domain AI platform. Team of 5-10. Need to ship fast, validate multiple use cases, keep burn low.

---

## Hybrid Approach (Best of Both Worlds)

You don't have to pick one. Here's a pragmatic hybrid:

### Start: Platform-First (MVP Stage)

```
Months 1-6: Build platform with 2-3 domains
- Aspora platform (executor, registry, RBAC)
- ECM domain (9 skills)
- Wealth domain (3 skills)
- Slack/WhatsApp channels

Team: 5 people
Cost: ~$50K infra + $600K team = $650K/year
Time to market: 2-3 months for platform + domains
```

### Validate: Add More Domains (Growth Stage)

```
Months 7-12: Add FinCrime, Fraud Guardian
- Onboard existing skills as domains
- Cross-domain workflows emerge
- Unified observability pays off

Team: 7 people
Cost: ~$70K infra + $840K team = $910K/year
Revenue: If generating revenue, platform leverage is clear
```

### Scale: Extract High-Value Domains (Scale-Up Stage)

```
Months 13-24: Extract Wealth as standalone product
- Wealth has 50K users, requires dedicated team
- Extract to separate backend (FastAPI/Go)
- Keep Wealth skills on platform for API integration
- Platform becomes "internal tool" for ECM/FinCrime

Team:
  - Platform (ECM/FinCrime): 5 people
  - Wealth Product: 8 people (2 FE, 3 BE, 1 mobile, 1 DevOps, 1 PM)
Total: 13 people

Cost: ~$150K infra + $1.56M team = $1.71M/year
Revenue: $5M+ ARR (Wealth is now a B2C SaaS product)
```

**Decision criteria for extraction**:
- Domain has > 10K active users
- Dedicated team can be justified (8+ people)
- Product-specific features outweigh platform reuse benefits
- Regulatory or blast radius concerns emerge

---

## Recommendation for Your Hackathon

### For Demo (36 hours): Platform-First

**Why**:
- Showcases innovation (multi-domain skills platform)
- Faster to build (reuse executor for 4 domains)
- Better story for judges (not just "another wealth app")
- Demonstrates technical depth (RBAC, context injection, OpenRouter)

**Constraints**:
- Accept higher complexity for demo impact
- Focus on static demo (reduce reliability risk)
- Pre-build critical pieces (executor, configs)

### For Production (next 6-12 months): Start Platform, Extract Later

**Phase 1 (Months 1-3)**: Platform with ECM + FinCrime
- Validate platform architecture with operations use cases
- Build out executor, RBAC, observability
- Team: 3-5 people

**Phase 2 (Months 4-6)**: Add Wealth domain to platform
- Onboard as 4th domain
- Start with basic portfolio features (static data)
- Team: +2 people (1 frontend, 1 skill dev)

**Phase 3 (Months 7-12)**: Evaluate extraction
- If Wealth traction > 10K users → extract to standalone product
- If Wealth is niche feature → keep on platform

**Phase 4 (Months 13+)**: Hybrid model
- Platform for operations teams (ECM, FinCrime)
- Standalone for consumer product (Wealth)
- Platform provides APIs that Wealth product calls

---

## Summary: The Honest Answer

| Aspect | Traditional | Platform | Verdict |
|--------|-------------|----------|---------|
| **Scalability** | Independent, clear scaling | Efficient but noisy neighbor risk | **Tie** (different patterns) |
| **Monitorability** | Simpler, per-product dashboards | Unified but complex traces | **Traditional** (simplicity wins) |
| **Reliability** | Better blast radius isolation | Shared fate risk | **Traditional** (safer) |
| **Development Speed (initial)** | Slower (rebuild infra per product) | Faster (shared platform) | **Platform** (10x faster) |
| **Development Speed (mature)** | Faster (isolated changes) | Slower (platform constraints) | **Traditional** (autonomy wins) |
| **Cost Efficiency** | Higher ($1.67M/year) | Lower ($1.00M/year) | **Platform** (40% savings) |
| **Team Structure** | Product teams (autonomous) | Platform + domain specialists | **Depends** (team size, culture) |
| **Innovation Speed** | Slow (new product = 3-4 months) | Fast (new domain = 1-2 weeks) | **Platform** (leverage) |

**For a hackathon demo**: Platform-First
**For a startup (< $1M ARR)**: Platform-First
**For a scale-up (> $5M ARR, 3+ established products)**: Traditional
**For long-term (2+ years)**: Hybrid (start Platform, extract high-value domains)

The platform approach is **NOT always better**. It trades blast radius and simplicity for cost efficiency and innovation speed. Pick based on your stage, team size, and risk tolerance.
