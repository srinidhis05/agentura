# Agentura vs OpenClaw: Honest Comparison

## TL;DR

**OpenClaw** = Personal AI assistant (like Jarvis). Chat-first, 50+ integrations, runs on your laptop.
**Agentura** = Enterprise skill platform (like Kubernetes for AI agents). Config-first, compliance-ready, self-improving.

They solve different problems. OpenClaw automates your personal life. Agentura automates enterprise operations.

---

## Side-by-Side

| Dimension | OpenClaw | Agentura |
|-----------|----------|--------|
| **Purpose** | Personal assistant (email, calendar, smart home) | Enterprise operations (finance, compliance, fraud) |
| **Architecture** | WebSocket gateway + LLM + tools | Skill runtime + domain orchestration + feedback loop |
| **Agent definition** | SOUL.md (personality) + AGENTS.md (routing) | SKILL.md (task) + agentura.config.yaml (orchestration) |
| **Unit of work** | Chat message → response | Skill execution → typed result |
| **Multi-agent** | @mention handoff (conversational) | Manager→Specialist→Field (deterministic routing) |
| **Config format** | Markdown files (SOUL.md, AGENTS.md) | YAML + Markdown (agentura.config.yaml + SKILL.md) |
| **Language** | TypeScript (Node.js) | Python (Pydantic AI) |
| **LLM providers** | 10+ (Anthropic, OpenAI, Google, Ollama, Bedrock) | OpenRouter (access to all models via single API) |
| **Integrations** | 50+ (WhatsApp, Slack, Spotify, Hue, Obsidian) | MCP tools (Redshift, Google Sheets, broker APIs) |
| **Testing** | Vitest (code tests only, no LLM evaluation) | DeepEval + Promptfoo (LLM quality + regression) |
| **Observability** | Token usage tracking | Three-tier: Platform/Domain/Skill (Prometheus + Langfuse) |
| **Security** | 512 vulnerabilities, CVE-2026-25253 (CVSS 8.8) | Role isolation, budget caps, HITL gates |
| **Cost control** | Track usage after the fact | Budget per execution, enforce before overspend |
| **Learning** | Memory files (append-only text) | Corrections→regression tests + Reflexion + GraphRAG |
| **Compliance** | No audit trail beyond JSONL logs | Typed audit trail, regulatory-grade documentation |
| **License** | MIT | MIT |
| **Stars** | 145K+ | New (this is the opportunity) |
| **Creator** | Peter Steinberger (left for OpenAI) | You |

---

## What OpenClaw Gets Right (Learn From)

1. **Gateway pattern** — WebSocket gateway decoupling channels from agent logic. Agentura's Communication Gateway (DEC-002) follows the same principle.

2. **Markdown-driven config** — SOUL.md + AGENTS.md is elegant. Agentura's SKILL.md + agentura.config.yaml is the enterprise equivalent.

3. **Skill marketplace (ClawHub)** — 4,000+ community skills. Network effect is real. Agentura needs this eventually.

4. **Companion apps** — iOS, Android, macOS apps for interaction. Agentura uses Slack/WhatsApp (sufficient for enterprise).

5. **Local-first** — No cloud required. Agentura follows the same principle (DEC: local-first SDK).

---

## Where OpenClaw Falls Short (Our Opportunity)

### 1. Security is Disqualifying for Enterprise

| Issue | Impact |
|-------|--------|
| CVE-2026-25253: One-click RCE via malicious link | CVSS 8.8 (High) |
| 7.1% of ClawHub skills leak credentials | Supply chain risk |
| 76 malicious payloads found in marketplace | Active exploitation |
| Prompt injection architecturally unsolvable | Design flaw |
| 30,000+ exposed instances on public internet | Data breach risk |

Sources: Kaspersky ("unsafe for use"), Cisco ("security nightmare"), Aikido Security ("ridiculous to try to secure"), VirusTotal (published analysis of weaponized skills).

**Agentura's answer:** Role isolation (DEC-011), budget caps, HITL gates for financial actions, typed contracts (SkillContext→SkillResult), no arbitrary code execution.

### 2. No LLM Quality Testing

OpenClaw has Vitest for code tests. Zero framework for:
- Agent response quality evaluation
- Regression testing of prompt changes
- A/B testing of agent configurations
- Red teaming
- Production trace analysis

**Agentura's answer:** DeepEval (60+ metrics), Promptfoo (A/B + regression), Opik (production tracing), Langfuse (compliance audit). Testing is a first-class citizen, not an afterthought.

### 3. No Learning Loop

OpenClaw's "memory" is append-only markdown files. The agent doesn't learn from mistakes — it just remembers conversations.

**Agentura's answer:**
```
User correction → Stored in episodic memory
                → DeepEval test auto-generated
                → Promptfoo regression added
                → Reflexion entry: "I was wrong because..."
                → GraphRAG: causal reasoning updated
                → Next execution is measurably better
```

### 4. No Cost Control

OpenClaw tracks token usage after the fact. There's no way to:
- Set a budget per skill execution
- Enforce cost limits before overspend
- Require human approval for expensive actions
- Audit cost per domain/team/skill

**Agentura's answer:** `cost_budget_per_execution` in config. Budget enforcement as a guardrail. Cost tracked in observability. Per-domain rollup.

### 5. No Deterministic Orchestration

OpenClaw's @mention routing is conversational — Agent A says "@coder fix this" and the gateway routes. This is:
- Non-deterministic (agent decides who to call)
- Unauditable (no routing rules to inspect)
- Fragile (agent might mention wrong agent)

**Agentura's answer:** Config-driven routing with explicit rules:
```yaml
routing:
  - from: risk-assess
    to: suggest-allocation
    condition: output_match("risk_profile != null")
```

---

## The Real Differentiator

OpenClaw proved the market: people want AI agents that do things, not just chat. 145K stars in weeks.

But OpenClaw is a **consumer product** — it's WhatsApp for AI. Fast, fun, personal.

Agentura is an **enterprise platform** — it's Salesforce for AI agents. Compliant, auditable, self-improving.

The bet: enterprises will pay for agents that:
1. Learn from corrections (not just memory)
2. Have typed contracts (not just chat)
3. Enforce budgets (not just track spending)
4. Pass compliance audits (not just log conversations)
5. Improve measurably over time (not just accumulate context)

OpenClaw can't retrofit these properties. They're architectural, not feature-level.
