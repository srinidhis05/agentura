# Agentura: Docker for AI Agents

> SKILL.md is the new Dockerfile.
> agentura.config.yaml is the new docker-compose.yaml.
> `agentura run` is the new `docker run`.

## The Analogy

| Docker | Agentura | What it does |
|--------|--------|-------------|
| `Dockerfile` | `SKILL.md` | Declares what to build |
| `docker build` | `agentura validate` | Validates the definition |
| `docker run` | `agentura run` | Executes it |
| `docker-compose.yaml` | `agentura.config.yaml` | Orchestrates multiple units |
| `docker-compose up` | `agentura up` | Runs a full domain |
| `docker test` / CI | `agentura test` | Regression + quality tests |
| `Docker Hub` | Skill Registry | Publish / discover / install |
| Kubernetes Operators | Knowledge Layer | Self-healing, self-improving |

## Why This Matters

Docker didn't invent containers. It invented **Dockerfile** — a format so simple anyone could learn it in 5 minutes. That format became the standard.

Kubernetes didn't invent orchestration. It invented **declarative YAML manifests** — describe desired state, the system makes it happen.

Agentura doesn't invent AI agents. It invents **a declarative format for agent skills** — describe what the agent does in SKILL.md, how it's orchestrated in agentura.config.yaml, and the runtime handles execution, testing, observability, and self-improvement.

## Build Iterations

Each iteration adds one Docker concept. Each one is working and demo-able.

| Iteration | Docker Parallel | What You Get |
|-----------|----------------|-------------|
| [01: Hello World](iterations/01-hello-world/) | `docker run hello-world` | One skill, one command, output |
| [02: Write Your Own](iterations/02-write-your-own/) | Write a `Dockerfile` | Create SKILL.md → validate → run |
| [03: Compose](iterations/03-compose/) | `docker-compose.yaml` | Multi-skill routing: Manager → Specialist |
| [04: Test](iterations/04-test/) | CI/CD pipeline | Corrections → auto-regression tests |
| [05: Knowledge](iterations/05-knowledge/) | Kubernetes Operators | Self-improving agents (Reflexion + GraphRAG) |
| [06: Registry](iterations/06-registry/) | Docker Hub | Publish / discover / install skills |

## Quick Start

```bash
# Install
pip install -e "sdk[test]"

# Iteration 1: Hello World
agentura run showcase/hello --dry-run

# Iteration 2: Write your own
agentura create skill demo/my-first --lang python --role specialist
# Edit skills/demo/my-first/SKILL.md
agentura validate demo/my-first
agentura run demo/my-first --dry-run

# Iteration 3: Compose (multi-skill domain)
agentura up showcase/wealth    # runs risk-assess → routes to suggest-allocation

# Iteration 4: Test
agentura test showcase/wealth  # corrections become regression tests

# Iteration 5: Knowledge
agentura run showcase/wealth --with-memory  # agent remembers past executions
```
