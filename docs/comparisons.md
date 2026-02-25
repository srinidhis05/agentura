# How Agentura Compares to Other Frameworks

> **Purpose**: Help you decide if Agentura is the right tool for your use case. Every framework has strengths — this doc explains where Agentura fits and where something else might be a better choice.

---

## The Short Version

Most agent frameworks are **libraries** — you import them into Python/TypeScript and write code to define agents. Agentura is a **platform** — you write skills in Markdown + YAML and deploy them into an orchestration layer that handles routing, isolation, security, and learning.

**Use Agentura when**: You need to deploy AI skills across multiple business domains with domain isolation, feedback-driven improvement, and non-developer skill authors.

**Use something else when**: You need a quick single-agent prototype, your team is all developers comfortable with code-first agents, or you need deep framework-specific integrations (LangChain ecosystem, Azure, etc.).

---

## Comparison Matrix

| Dimension | CrewAI | LangGraph | AutoGen | PydanticAI | Mastra | n8n | **Agentura** |
|-----------|--------|-----------|---------|------------|--------|-----|-------------|
| **Architecture** | Code-first (Python) | Code-first (state graphs) | Code-first (conversations) | Code-first (Python + types) | Code-first (TypeScript) | Visual workflow builder | **Config-first (Markdown + YAML)** |
| **Skill definition** | `Agent(role=, goal=, backstory=)` | `StateGraph().add_node()` | `ConversableAgent()` | `Agent(model, system_prompt)` | `Agent({ ... })` | Visual nodes | **SKILL.md + agentura.config.yaml** |
| **Multi-agent** | Crew with role hierarchy | Graph with conditional edges | Conversation patterns | Single agent | Agent networks | Workflow connections | **Domain → Role → Skill hierarchy** |
| **Learning from feedback** | Memory (short/long/entity) | Checkpointing | Teachable agents (basic) | None | None | None | **Correction → auto-test → reflexion** |
| **Security model** | Basic (AMP adds RBAC) | Sandboxing via Pyodide | Basic | Type-safe outputs | Basic | Credential store | **Skills reason only; MCP tools act (separate boundary, MCP gateway planned)** |
| **Who writes skills** | Python developers | Python developers | Python/.NET developers | Python developers | TypeScript developers | No-code users | **Domain experts (Markdown)** |

---

## Detailed Comparisons

### vs CrewAI

CrewAI is the most mature multi-agent framework with a strong enterprise offering (AMP).

**CrewAI strengths**: Role-based orchestration, memory system (ChromaDB/SQLite), AMP platform for enterprise RBAC and audit logs, large community.

**Different approach in Agentura**:
- **Config vs Code**: CrewAI agents are Python classes. Agentura skills are Markdown files with YAML config. This means domain experts (not just developers) can author and maintain skills.
- **Learning loop**: CrewAI stores memory context. Agentura auto-generates regression tests from every user correction, creating a growing test suite that prevents regressions.
- **Domain isolation**: CrewAI crews are flat. Agentura organizes skills into domains with namespace-scoped resource quotas and cross-domain policies.

**Choose CrewAI if**: Your team is Python-heavy, you want a mature ecosystem, and code-first agents work for your workflow.

---

### vs LangGraph / LangChain

LangGraph is the most flexible graph-based agent framework, backed by the LangChain ecosystem.

**LangGraph strengths**: Flexible state graph model, checkpointing, human-in-the-loop via state persistence, deep LangChain ecosystem, LangSmith for observability.

**Different approach in Agentura**:
- **Abstraction level**: LangGraph is a graph execution engine — you wire Python nodes. Agentura is a platform — skills are Markdown, routing is config-driven.
- **Security**: LangGraph relies on external tools for PII/secrets scanning. Agentura's architecture separates reasoning (skills) from action (MCP tools), with an MCP gateway layer planned for policy enforcement (PII scanning, secrets detection, injection prevention).
- **Bundled platform features**: LangSmith (paid) provides observability. Agentura bundles observability, domain isolation, learning loops, and cost governance together.

**Choose LangGraph if**: You need fine-grained control over agent execution flow, want to build custom agent architectures, or are already invested in the LangChain ecosystem.

---

### vs AutoGen / Microsoft Agent Framework

AutoGen pioneered multi-agent conversation patterns and is being absorbed into Microsoft Agent Framework.

**AutoGen strengths**: Multi-agent conversations (group chat, nested), Microsoft/Azure backing, Semantic Kernel integration, long-term memory via Foundry Agent Service.

**Different approach in Agentura**:
- **Philosophy**: AutoGen is conversation-centric (agents talk to each other). Agentura is task-centric (skills receive input, produce output, learn from corrections).
- **Vendor independence**: MS Agent Framework targets Azure-first enterprises. Agentura is cloud-agnostic.

**Choose AutoGen/MS Agent Framework if**: You're on Azure, need conversation-based multi-agent patterns, or want Microsoft enterprise support.

---

### vs PydanticAI

PydanticAI is a type-safe agent library with excellent structured output support and MCP integration.

**PydanticAI strengths**: Type-safe structured outputs, native MCP support, clean Pythonic API, minimal footprint.

**Relationship**: Agentura uses PydanticAI as its execution engine. PydanticAI handles the LLM call; Agentura handles everything around it (routing, domain isolation, learning, security, deployment).

**Choose PydanticAI directly if**: You need a lightweight agent library in a Python application and don't need multi-domain orchestration or feedback loops.

---

### vs n8n

n8n is a visual workflow automation platform — a different category entirely.

| | n8n | Agentura |
|---|-----|----------|
| **What it is** | Visual workflow builder (if-this-then-that with AI nodes) | AI skill orchestration platform |
| **Paradigm** | Deterministic workflows with optional AI steps | AI-native skills with optional deterministic routing |
| **Skills** | Workflow nodes (fixed input → fixed output) | LLM-powered reasoning (structured input → reasoned output) |
| **Learning** | None — workflows are static | Correction → test → reflexion pipeline |
| **Best for** | Automating repetitive processes | Domain-specific AI reasoning at scale |

**They're complementary**: n8n can trigger Agentura skills as workflow steps, and Agentura can call n8n workflows via MCP tools.

---

### vs Pi.dev

Pi.dev is a minimal terminal coding agent — a "coding harness" with a primitives-over-features philosophy.

**Pi.dev strengths**: Multi-provider support (15+ providers), tree-structured session history, four operational modes (TUI, print, RPC, SDK), extensible via TypeScript skills and prompt templates.

**Different category**: Pi.dev is a developer coding tool (like Cursor or Claude Code). Agentura is a skill orchestration platform. Pi.dev helps a developer write code interactively; Agentura deploys domain-specific AI skills that business teams author and that improve from feedback. They solve different problems.

---

### vs Agno, SmolAgents, Mastra, Atomic Agents

These are newer agent libraries, each with a specific focus:

| Framework | Language | Focus | How Agentura Differs |
|-----------|----------|-------|---------------------|
| **Agno** (ex-Phidata) | Python | Multi-modal agents, tool-use | Library vs platform — no orchestration layer |
| **SmolAgents** | Python | HuggingFace ecosystem, code-gen agents | Research-oriented, not enterprise multi-domain |
| **Mastra** | TypeScript | TS-native agents with observability | Strong for TS teams, but no learning loop or domain isolation |
| **Atomic Agents** | Python | Composable, minimal primitives | Clean design, but library-level — no platform features |

**Key distinction**: All of these are libraries you import. Agentura is a platform you deploy into. If you need a quick agent in your app, use a library. If you need to manage skills across business domains with feedback loops and governance, use a platform.

---

## What Makes Agentura Different

### 1. Correction → Test → Reflexion Pipeline
No framework auto-generates regression tests from user corrections. When a user corrects a skill's output, Agentura stores the correction, generates a test case, and creates a reflexion entry that the skill applies on future executions. Over time, skills get measurably better.

### 2. 4-Layer Prompt Hierarchy
```
WORKSPACE.md  → Organization-wide rules (all skills, all domains)
DOMAIN.md     → Domain identity & voice (per domain)
Reflexions    → Learned rules from corrections (per skill, auto-generated)
SKILL.md      → Task-specific prompt (per skill)
```
No framework separates organizational context from domain context from learned rules from task instructions.

### 3. Domain-as-Namespace Isolation
Skills are organized into domains with resource quotas, cross-domain policies, and role-based access. Each domain is isolated — skills in different domains cannot access each other's data directly.

### 4. Structural Security
Skills produce text/JSON only — they cannot execute code or shell commands. Real-world actions go through MCP tools via a separate boundary. An MCP gateway layer (planned) will add policy enforcement — PII scanning, secrets detection, and injection prevention — before tool calls reach external systems. The reasoning/action separation is architectural, not policy-based.

### 5. Config-Driven, Not Code-Driven
A domain expert writes a SKILL.md in Markdown and an agentura.config.yaml. No Python, TypeScript, or Go required to create a skill. Code is only needed for custom execution handlers.

---

## When NOT to Use Agentura

Be honest about fit:

- **Quick prototype**: If you need a single agent in 20 lines of Python, use PydanticAI or CrewAI directly.
- **Deep LLM framework integration**: If you need LangChain retrievers, chains, and the full ecosystem, use LangGraph.
- **Azure enterprise**: If your org is Azure-first and wants Microsoft support, use MS Agent Framework.
- **Visual workflows**: If your team prefers drag-and-drop over config files, use n8n.
- **Research/experimentation**: If you're exploring novel agent architectures, use SmolAgents or LangGraph for flexibility.

Agentura is purpose-built for **multi-domain enterprise AI skill orchestration with feedback-driven improvement**. If that's not your use case, something simpler will serve you better.
