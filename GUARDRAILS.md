# Aspora Platform — Guardrails (Anti-Patterns)

> **Purpose**: Record mistakes and anti-patterns to prevent repetition.
> **Format**: `Mistake → Impact → Rule → Detection`

---

## GRD-001: Scope Creep in Hackathon Planning

**Mistake**: Planned 14 skills across 3 domains for a hackathon demo.
**Impact**: Zero working demos. Hours spent on architecture slides instead of building.
**Rule**: Hackathon primitive = ONE working loop, not breadth. Slides for breadth, live demo for depth.
**Detection**: If planning touches >3 skills before any are running, STOP and narrow.
**Date**: 2026-02-17

---

## GRD-002: Positioning Churn Burns Cycles

**Mistake**: Shifted framing 3x in one session (Docker → K8s → Swarm → back to K8s).
**Impact**: Code written for wrong framing had to be discarded. Showcase restructured twice.
**Rule**: Lock positioning BEFORE writing showcase code. Ideation and coding are separate phases.
**Detection**: If analogy/framing changes mid-implementation, pause coding and finish ideation first.
**Date**: 2026-02-17

---

## GRD-003: Never Trust Marketing Claims from AI Agent Frameworks

**Mistake**: Almost positioned against Swarms/ClawSwarm before deep code review.
**Impact**: Would have over-estimated competitor. ClawSwarm is single-agent chatbot despite "multi-agent swarm" marketing. `agent.py` is 6,165-line god class. Tests never pass in CI.
**Rule**: ALWAYS read competitor source code before competitive positioning. Marketing ≠ engineering.
**Detection**: Any competitive claim without link to specific source file = unverified.
**Date**: 2026-02-17

---

## GRD-004: Don't Code During Ideation

**Mistake**: Started writing showcase iteration files while user was still exploring positioning.
**Impact**: Files written for wrong framing. User had to explicitly say "stop writing code."
**Rule**: When user says "ideating" or "thinking mode", respond with analysis only. No file writes.
**Detection**: If user message contains "ideating", "thinking", "brainstorming" → NO tool calls that write files.
**Date**: 2026-02-17

---

## GRD-005: Never Build Python Code for What Should Be a Skill

**Mistake**: Built a `PlatformRouter` Python class with pattern matching and `DomainAdapter` classes for domain routing.
**Impact**: Created Python code that contradicts the "everything is a skill" architecture. The routing logic should live in SKILL.md and plugin.yaml, not Python classes.
**Rule**: Python/Pydantic AI is ONLY the execution engine. Routing, domain logic, business rules, knowledge — ALL live in skills (SKILL.md) and config (plugin.yaml, aspora.config.yaml). If you're writing Python that decides WHERE to route, STOP — make it a skill.
**Detection**: If a Python file contains routing logic, domain classification, or business rules → it should be a SKILL.md or config file instead.
**Date**: 2026-02-18

---

## GRD-006: MCP for Structured Data, Not RAG

**Mistake**: Considered RAG infrastructure for data that's already in Redshift/Databricks with known schemas.
**Impact**: Would have built probabilistic approximate search for data that needs deterministic exact queries.
**Rule**: Structured data in databases → MCP (precise SQL). Knowledge that fits in context → Skills (SKILL.md + config YAML). RAG only for unstructured docs exceeding context window.
**Detection**: If proposing RAG for data in Redshift/Databricks/PostgreSQL → STOP, use MCP instead.
**Date**: 2026-02-18

---

## When to Add Guardrails

- **Mistake caught** → GRD-NNN
- **Anti-pattern discovered** → GRD-NNN
- **User explicitly flags bad practice** → GRD-NNN

Keep entries actionable. Every guardrail MUST have a Detection rule.

---

## GRD-007: Surface-Level K8s Analogies Without Operational Depth

**Mistake**: Built UI pages that use K8s vocabulary (namespaces, pods, workloads) but lacked operational controls — no deploy status, no canary indicators, no resource quotas, no event stream.
**Impact**: Dashboard looked like K8s but felt like a skill browser. User correctly identified it as missing the real vision.
**Rule**: K8s analogy requires operational controls, not just organizational labels. Every "K8s-like" page must have: health indicators, deploy status, resource limits, event history, and actionable controls.
**Detection**: If a page uses K8s terminology but has no health dots, no status badges, no budget gauges, and no event timeline — it's a label, not a control plane.
**Date**: 2026-02-20

---

## GRD-008: Consultant Mode — Listing Problems Instead of Fixing Them

**Mistake**: When asked "is it open-source worthy?", responded with a 3-week roadmap of gaps instead of immediately building the fixes. Estimated timelines for work that could be done in one session.
**Impact**: User had to call it out twice. Zero code written while paragraphs of analysis were produced. Builder velocity dropped to zero.
**Rule**: Identify the gap, then BUILD THE FIX in the same response. Never list more than 3 problems without immediately solving the first one. If you can build it tonight, don't say "Week 1/Week 2/Week 3".
**Detection**: If response contains timeline estimates (days/weeks) without tool calls that write code — STOP and start building.
**Date**: 2026-02-20
