export default function LandingPage() {
  return (
    <div className="min-h-screen text-foreground">
      <Nav />
      <Hero />
      <CompoundingIntelligence />
      <HowItWorks />
      <MemoryLearning />
      <ExecutorTypes />
      <Architecture />
      <PortYourPlugins />
      <WhySelfHost />
      <GetStarted />
      <Footer />
    </div>
  );
}

/* ── Navigation ── */

function Nav() {
  return (
    <nav className="fixed top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-violet-600">
            <svg className="h-3.5 w-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span className="text-base font-bold tracking-tight">Agentura</span>
        </div>

        <div className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
          <a href="#how-it-learns" className="transition-colors hover:text-foreground">How It Learns</a>
          <a href="#how-it-works" className="transition-colors hover:text-foreground">How It Works</a>
          <a href="#executors" className="transition-colors hover:text-foreground">Executors</a>
          <a href="#architecture" className="transition-colors hover:text-foreground">Architecture</a>
          <a href="#port-plugins" className="transition-colors hover:text-foreground">Port Plugins</a>
        </div>

        <a
          href="https://github.com/srinidhis05/agentura"
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-lg border border-border px-4 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:border-foreground/20 hover:text-foreground"
        >
          GitHub
        </a>
      </div>
    </nav>
  );
}

/* ── Hero ── */

function Hero() {
  return (
    <section className="relative overflow-hidden pt-32 pb-20 md:pt-44 md:pb-32">
      {/* Radial glow */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="h-[600px] w-[800px] rounded-full bg-gradient-radial from-blue-500/8 via-violet-500/4 to-transparent blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-4xl px-6 text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border/60 bg-card/50 px-4 py-1.5 text-xs text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Kubernetes-native &middot; Self-hosted &middot; Apache 2.0
        </div>

        <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl md:leading-[1.1]">
          AI That Gets Smarter{" "}
          <br className="hidden md:block" />
          &mdash; And Stays Yours
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl">
          Cloud AI forgets you between sessions. Agentura remembers everything &mdash;
          corrections become reflexion rules, reflexions become system prompts, and every
          execution deepens a knowledge base that lives on your infrastructure, not someone else&apos;s.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a
            href="#get-started"
            className="rounded-lg px-6 py-2.5 text-sm font-semibold transition-colors"
            style={{
              backgroundColor: "oklch(0.72 0.17 45)",
              color: "oklch(0.98 0 0)",
            }}
          >
            Get Started
          </a>
          <a
            href="#memory-moat"
            className="rounded-lg border border-border px-6 py-2.5 text-sm font-semibold text-muted-foreground transition-colors hover:border-foreground/20 hover:text-foreground"
          >
            See How It Learns
          </a>
        </div>
      </div>
    </section>
  );
}

/* ── Memory Moat ── */

function CompoundingIntelligence() {
  return (
    <section id="how-it-learns" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-5xl px-6">
        <div className="grid gap-10 md:grid-cols-2 md:items-center">
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-purple-400">
              Intelligence That Compounds
            </p>
            <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
              The longer you use it,{" "}
              <br className="hidden md:block" />
              the smarter it gets
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              Every correction your team makes becomes a permanent guardrail.
              Every reflexion rule gets injected into future prompts automatically.
              Six months in, your system knows your domain better than any vendor
              ever could &mdash; and that knowledge can never be taken from you.
            </p>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              After six months, your system has thousands of domain-specific
              learnings that no vendor can replicate &mdash; because they live on
              your infrastructure and belong to you.
            </p>
          </div>

          <div className="space-y-3">
            <MoatStep
              week="Week 1"
              label="First corrections"
              detail="Team corrects agent output. System stores corrections in PostgreSQL."
              fill="w-[15%]"
              color="from-purple-500/60 to-purple-500/30"
            />
            <MoatStep
              week="Month 1"
              label="Reflexion rules active"
              detail="Corrections generate reflexions. Agents stop repeating the same mistakes."
              fill="w-[35%]"
              color="from-purple-500/70 to-blue-500/40"
            />
            <MoatStep
              week="Month 3"
              label="Domain expertise emerges"
              detail="Hundreds of learnings. Agents know your naming conventions, preferences, edge cases."
              fill="w-[65%]"
              color="from-blue-500/70 to-cyan-500/40"
            />
            <MoatStep
              week="Month 6+"
              label="Institutional memory"
              detail="Thousands of domain-specific guardrails. No vendor can replicate this. It's yours."
              fill="w-[90%]"
              color="from-cyan-500/70 to-emerald-500/50"
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function MoatStep({
  week,
  label,
  detail,
  fill,
  color,
}: {
  week: string;
  label: string;
  detail: string;
  fill: string;
  color: string;
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/50 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-muted-foreground">{week}</span>
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-secondary/80">
        <div className={`h-2 rounded-full bg-gradient-to-r ${color} ${fill}`} />
      </div>
      <p className="mt-2 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}

/* ── How It Works ── */

function HowItWorks() {
  const steps = [
    {
      num: "1",
      title: "Write a Skill",
      desc: "Define your agent in SKILL.md (Markdown) and agentura.config.yaml. Pick an executor type, wire MCP tools, set budgets.",
      code: `---
name: deployer
role: agent
domain: dev
model: anthropic/claude-sonnet-4-5
---

# Deployer Agent
You receive app artifacts and deploy
them to Kubernetes via kubectl.`,
      color: "text-emerald-400",
      borderColor: "border-emerald-500/30",
    },
    {
      num: "2",
      title: "Chain into Pipelines",
      desc: "Compose skills into multi-step pipelines. Each step's output flows as context to the next. Define once in YAML.",
      code: `name: build-deploy
steps:
  - skill: dev/app-builder  # builds app
  - skill: dev/deployer     # deploys to K8s

# app-builder artifacts automatically
# flow to deployer as input`,
      color: "text-blue-400",
      borderColor: "border-blue-500/30",
    },
    {
      num: "3",
      title: "Execute in Isolated Pods",
      desc: "Each agent runs in its own K8s pod with bounded CPU, memory, and API budget. Pod is created per-execution and destroyed after.",
      code: `agent:
  executor: ptc          # or claude-code
  timeout: 120
  max_iterations: 15
  max_tokens: 16384

mcp_tools:
  - server: k8s
    tools: [kubectl_apply, kubectl_get]`,
      color: "text-amber-400",
      borderColor: "border-amber-500/30",
    },
    {
      num: "4",
      title: "Learn and Improve",
      desc: "Corrections become regression tests. Reflexion rules are injected into future prompts. Memory recall applies learned preferences automatically.",
      code: `# User corrects: "use dark theme"
# System generates:
correction: "Always use dark theme"
reflexion: "User prefers dark mode with
  purple accent (#8b5cf6). Apply this
  theme to all UI builds."

# Next execution auto-recalls this.`,
      color: "text-purple-400",
      borderColor: "border-purple-500/30",
    },
  ];

  return (
    <section id="how-it-works" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            How It Works
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            From Markdown skill definition to production deployment in four steps
          </p>
        </div>

        <div className="space-y-6">
          {steps.map((step) => (
            <div
              key={step.num}
              className={`rounded-xl border ${step.borderColor} bg-card/50 p-6 shadow-lg`}
            >
              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`flex h-8 w-8 items-center justify-center rounded-full border ${step.borderColor} text-sm font-bold ${step.color}`}>
                      {step.num}
                    </span>
                    <h3 className="text-lg font-semibold">{step.title}</h3>
                  </div>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {step.desc}
                  </p>
                </div>
                <div className="overflow-hidden rounded-lg border border-border bg-background/50">
                  <div className="flex items-center gap-1.5 border-b border-border px-3 py-1.5">
                    <span className="h-2 w-2 rounded-full bg-red-500/50" />
                    <span className="h-2 w-2 rounded-full bg-amber-500/50" />
                    <span className="h-2 w-2 rounded-full bg-emerald-500/50" />
                  </div>
                  <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-muted-foreground">
                    <code>{step.code}</code>
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Executor Types ── */

function ExecutorTypes() {
  const executors = [
    {
      name: "PTC Worker",
      tag: "executor: ptc",
      desc: "Programmatic Tool Calling. Lightweight Python-only pod (~200MB) that runs an Anthropic tool-calling loop and dispatches tools to MCP servers. Ideal for orchestration tasks like K8s deployment, API workflows, and data pipelines.",
      specs: ["1 CPU, 512Mi RAM", "Python-only, no Node.js", "Direct MCP tool dispatch", "Auto-configurable max_tokens"],
      useCases: ["K8s deployer", "API orchestration", "Data pipelines"],
      color: "amber",
    },
    {
      name: "Claude Code Worker",
      tag: "executor: claude-code",
      desc: "Full Claude Agent SDK in an isolated pod (~800MB). Has file I/O, bash execution, and code editing tools. Used for skills that need to write code, run builds, or manipulate files in a sandbox.",
      specs: ["2 CPU, 2Gi RAM", "Python + Node.js 20", "File read/write/edit + Bash", "Artifact extraction to pipeline"],
      useCases: ["App builder", "Code generator", "Build + test runner"],
      color: "blue",
    },
    {
      name: "Legacy Executor",
      tag: "No executor field",
      desc: "In-process execution via Pydantic AI. No worker pod — runs directly in the executor process. Best for simple prompt-response skills that don't need tools or sandboxing.",
      specs: ["No extra pod", "Pydantic AI + Anthropic", "OpenRouter fallback", "Minimal latency"],
      useCases: ["Email drafter", "Summarizer", "Classifier"],
      color: "emerald",
    },
  ];

  const colorMap = {
    amber: { border: "border-amber-500/30", label: "text-amber-400", tag: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    blue: { border: "border-blue-500/30", label: "text-blue-400", tag: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
    emerald: { border: "border-emerald-500/30", label: "text-emerald-400", tag: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
  };

  return (
    <section id="executors" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Three Executor Types
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Right-sized isolation for every workload. Each agent skill picks its executor in config.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {executors.map((exec) => {
            const c = colorMap[exec.color as keyof typeof colorMap];
            return (
              <div key={exec.name} className={`rounded-xl border ${c.border} bg-card/50 p-6 shadow-lg flex flex-col`}>
                <div className="mb-3 flex items-center justify-between">
                  <h3 className={`text-base font-semibold ${c.label}`}>{exec.name}</h3>
                </div>
                <code className={`inline-block self-start rounded-md border px-2 py-0.5 text-xs font-mono mb-4 ${c.tag}`}>
                  {exec.tag}
                </code>
                <p className="text-sm leading-relaxed text-muted-foreground mb-4">
                  {exec.desc}
                </p>
                <div className="mt-auto space-y-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/60 mb-2">Specs</p>
                    <div className="flex flex-wrap gap-1.5">
                      {exec.specs.map((s) => (
                        <span key={s} className="rounded-md bg-secondary/80 px-2 py-0.5 text-xs text-muted-foreground">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/60 mb-2">Use Cases</p>
                    <div className="flex flex-wrap gap-1.5">
                      {exec.useCases.map((u) => (
                        <span key={u} className="rounded-md bg-secondary/80 px-2 py-0.5 text-xs text-muted-foreground">
                          {u}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ── Architecture Diagram ── */

function Architecture() {
  return (
    <section id="architecture" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Architecture
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Go gateway for policy &middot; Python executor for orchestration &middot; K8s pods for agent isolation
          </p>
        </div>

        <div className="mx-auto max-w-5xl space-y-4">
          {/* Top row: User + Operator */}
          <div className="grid gap-4 md:grid-cols-2">
            <ArchBox
              label="User / Chat Client"
              items={["Chat UI", "CLI", "Slack", "REST API"]}
              borderColor="border-emerald-500/30"
              labelColor="text-emerald-400"
              glow="shadow-emerald-500/5"
            />
            <ArchBox
              label="Operator / SRE"
              items={["agentura CLI", "Dashboard", "Pipeline YAML", "Alerts"]}
              borderColor="border-emerald-500/30"
              labelColor="text-emerald-400"
              glow="shadow-emerald-500/5"
            />
          </div>

          {/* Connection line down */}
          <div className="flex justify-center">
            <div className="flex flex-col items-center gap-1">
              <div className="h-6 w-px bg-gradient-to-b from-emerald-500/40 to-blue-500/40" />
              <span className="text-[10px] text-muted-foreground">HTTP + SSE streaming</span>
              <div className="h-6 w-px bg-gradient-to-b from-blue-500/40 to-blue-500/20" />
            </div>
          </div>

          {/* Control Plane */}
          <div className="rounded-xl border border-blue-500/30 bg-blue-500/[0.03] p-5 shadow-lg shadow-blue-500/5">
            <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-blue-400">
              Control Plane &middot; Go Gateway
            </p>
            <div className="grid gap-3 sm:grid-cols-4">
              <InnerBox label="API Server" sub="HTTP + SSE" color="blue" />
              <InnerBox label="Auth + CORS" sub="Rate Limiting" color="blue" />
              <InnerBox label="Admission Control" sub="Budget + Model Gate" color="blue" />
              <InnerBox label="Pipeline Router" sub="Step Orchestration" color="blue" />
            </div>
          </div>

          {/* Connection line */}
          <div className="flex justify-center">
            <div className="h-8 w-px bg-gradient-to-b from-blue-500/40 to-amber-500/40" />
          </div>

          {/* Executor */}
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.03] p-5 shadow-lg shadow-amber-500/5">
            <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-amber-400">
              Skill Executor &middot; Python
            </p>
            <div className="grid gap-3 sm:grid-cols-4">
              <InnerBox label="Executor Router" sub="PTC / CC / Legacy" color="amber" />
              <InnerBox label="Skill Loader" sub="SKILL.md + Config" color="amber" />
              <InnerBox label="Pipeline Engine" sub="carry_forward" color="amber" />
              <InnerBox label="Memory Recall" sub="Prompt Injection" color="amber" />
            </div>
          </div>

          {/* Connection lines down to worker pods */}
          <div className="flex justify-center">
            <div className="flex flex-col items-center gap-1">
              <div className="h-6 w-px bg-gradient-to-b from-amber-500/40 to-rose-500/40" />
              <span className="text-[10px] text-muted-foreground">creates per-execution pods</span>
              <div className="h-6 w-px bg-gradient-to-b from-rose-500/40 to-rose-500/20" />
            </div>
          </div>

          {/* Worker Pods */}
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/[0.03] p-5 shadow-lg shadow-rose-500/5">
            <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-rose-400">
              Agent Pods &middot; Kubernetes
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              <InnerBox label="PTC Worker" sub="~200MB, MCP tools" color="rose" />
              <InnerBox label="Claude Code Worker" sub="~800MB, file I/O + bash" color="rose" />
              <InnerBox label="Deployed Apps" sub="nginx, node, python" color="rose" />
            </div>
          </div>

          {/* Connection lines down */}
          <div className="flex justify-center">
            <div className="h-8 w-px bg-gradient-to-b from-rose-500/40 to-transparent" />
          </div>

          {/* Horizontal distribution */}
          <div className="mx-auto hidden max-w-3xl md:block">
            <div className="h-px bg-gradient-to-r from-transparent via-muted-foreground/20 to-transparent" />
          </div>

          {/* Bottom row */}
          <div className="grid gap-4 md:grid-cols-4">
            <ArchBox
              label="Skills Directory"
              items={["SKILL.md", "Config YAML", "Pipelines", "Tests"]}
              borderColor="border-emerald-500/30"
              labelColor="text-emerald-400"
              glow="shadow-emerald-500/5"
            />
            <ArchBox
              label="MCP Servers"
              items={["kubectl", "Slack", "GitHub", "Custom"]}
              borderColor="border-cyan-500/30"
              labelColor="text-cyan-400"
              glow="shadow-cyan-500/5"
            />
            <ArchBox
              label="Knowledge Layer"
              items={["Reflexions", "Corrections", "Memory Store"]}
              borderColor="border-purple-500/30"
              labelColor="text-purple-400"
              glow="shadow-purple-500/5"
            />
            <ArchBox
              label="Storage"
              items={["PostgreSQL", "Artifacts Dir", "Shared Volumes"]}
              borderColor="border-orange-500/30"
              labelColor="text-orange-400"
              glow="shadow-orange-500/5"
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function ArchBox({
  label,
  items,
  borderColor,
  labelColor,
  glow,
}: {
  label: string;
  items: string[];
  borderColor: string;
  labelColor: string;
  glow: string;
}) {
  return (
    <div className={`rounded-xl border ${borderColor} bg-card/50 p-4 shadow-lg ${glow}`}>
      <p className={`mb-2 text-xs font-semibold uppercase tracking-widest ${labelColor}`}>
        {label}
      </p>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className="rounded-md bg-secondary/80 px-2.5 py-1 text-xs text-muted-foreground"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function InnerBox({
  label,
  sub,
  color,
}: {
  label: string;
  sub: string;
  color: "blue" | "amber" | "rose";
}) {
  const borderMap = { blue: "border-blue-500/20", amber: "border-amber-500/20", rose: "border-rose-500/20" };
  return (
    <div className={`rounded-lg border ${borderMap[color]} bg-background/50 px-4 py-3`}>
      <p className="text-sm font-medium">{label}</p>
      <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>
    </div>
  );
}

/* ── Memory & Learning ── */

function MemoryLearning() {
  return (
    <section id="memory" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            How the Memory System Works
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Three mechanisms that compound: reflexion rules, correction pipelines, and cross-domain recall
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-xl border border-purple-500/30 bg-card/50 p-6 shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <h3 className="text-base font-semibold">Reflexion Rules</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              When an agent makes a mistake and you correct it, the system generates a reflexion rule.
              This rule is automatically injected into the agent&apos;s system prompt on future runs &mdash;
              the same mistake never happens twice.
            </p>
            <div className="mt-4 rounded-lg border border-border bg-background/50 p-3">
              <pre className="font-mono text-xs text-muted-foreground leading-relaxed">{`reflexion: "User prefers dark mode
with purple accent (#8b5cf6).
Apply to all UI builds."

# Injected at TOP of system prompt
# before every app-builder run`}</pre>
            </div>
          </div>

          <div className="rounded-xl border border-cyan-500/30 bg-card/50 p-6 shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h3 className="text-base font-semibold">Correction &rarr; Test Pipeline</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Every correction is stored in PostgreSQL. Corrections auto-generate regression tests
              that guard against repeat failures. After 6 months of use, your skills accumulate
              thousands of domain-specific guardrails.
            </p>
            <div className="mt-4 rounded-lg border border-border bg-background/50 p-3">
              <pre className="font-mono text-xs text-muted-foreground leading-relaxed">{`correction → regression test
regression test → reflexion rule
reflexion rule → prompt injection

# Compounding improvement loop`}</pre>
            </div>
          </div>

          <div className="rounded-xl border border-amber-500/30 bg-card/50 p-6 shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold">Cross-Domain Memory</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Memory recall searches across all domains to find relevant past learnings.
              A preference set during a dev/app-builder run is available to hr/interview-questions
              if relevant. Stored in PostgreSQL, searchable by semantic similarity.
            </p>
            <div className="mt-4 rounded-lg border border-border bg-background/50 p-3">
              <pre className="font-mono text-xs text-muted-foreground leading-relaxed">{`# Memory injected at TOP of prompt:
## Memory (from past executions)
- Theme: dark mode, #8b5cf6
- Stack: vanilla JS preferred
- Style: minimal, modern

---
# Original SKILL.md follows...`}</pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Port Your Plugins ── */

function PortYourPlugins() {
  return (
    <section id="port-plugins" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Port Any Work Plugin in Minutes
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Existing runbooks, automation scripts, and work plugins become Agentura skills with zero code changes
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Before */}
          <div className="rounded-xl border border-border/60 bg-card p-6">
            <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-red-400">Before &mdash; Scattered Automation</p>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-red-400/60">&#x2717;</span>
                Runbooks in Confluence nobody reads
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-red-400/60">&#x2717;</span>
                Python scripts on someone&apos;s laptop
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-red-400/60">&#x2717;</span>
                Slack workflows that break silently
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-red-400/60">&#x2717;</span>
                No memory &mdash; same mistakes repeated
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-red-400/60">&#x2717;</span>
                No audit trail, no cost tracking
              </li>
            </ul>
          </div>

          {/* After */}
          <div className="rounded-xl border border-emerald-500/30 bg-card p-6">
            <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-emerald-400">After &mdash; Agentura Skills</p>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-emerald-400">&#x2713;</span>
                SKILL.md is the runbook &mdash; executable, versioned, tested
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-emerald-400">&#x2713;</span>
                Runs in isolated K8s pods, not laptops
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-emerald-400">&#x2713;</span>
                MCP tools connect to Slack, GitHub, K8s, DBs
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-emerald-400">&#x2713;</span>
                Memory recalls past corrections automatically
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 text-emerald-400">&#x2713;</span>
                Every execution logged with cost, latency, outcome
              </li>
            </ul>
          </div>
        </div>

        {/* Conversion steps */}
        <div className="mt-10 rounded-xl border border-border/60 bg-card p-6">
          <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Three-file conversion
          </p>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-border bg-background/50 p-4">
              <p className="text-sm font-semibold mb-2">1. SKILL.md</p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Paste your runbook as the system prompt. Add frontmatter (name, role, domain, model).
                The agent follows the instructions exactly as written.
              </p>
            </div>
            <div className="rounded-lg border border-border bg-background/50 p-4">
              <p className="text-sm font-semibold mb-2">2. agentura.config.yaml</p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Pick executor type (ptc/claude-code/legacy). Wire MCP tools.
                Set budget limits and iteration caps. Define display metadata.
              </p>
            </div>
            <div className="rounded-lg border border-border bg-background/50 p-4">
              <p className="text-sm font-semibold mb-2">3. Pipeline YAML (optional)</p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Chain skills into multi-step workflows. Each step&apos;s output
                auto-flows to the next via carry_forward. Define once, run anywhere.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Why Self-Host ── */

function WhySelfHost() {
  const reasons = [
    {
      title: "Your Data Never Leaves",
      copy: "Skills run in your K8s cluster. Prompts, responses, artifacts, and domain knowledge stay inside your network. Agent pods are ephemeral — created per-execution, destroyed after.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
    },
    {
      title: "No Vendor Lock-In",
      copy: "Skills are Markdown. Config is YAML. Swap Claude for GPT, Gemini, or a local model via OpenRouter — skills, memory, and the knowledge layer stay the same.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      ),
    },
    {
      title: "Domain Isolation Built In",
      copy: "Finance skills can't see HR data. Dev tools can't access production credentials. Each domain has its own RBAC, budget limits, MCP tool bindings, and admission policies.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
    },
    {
      title: "Cost Control Per Execution",
      copy: "Every skill has a budget cap. Every execution is logged with cost, latency, model used, and outcome. No surprise bills — agents are bounded by design.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];

  return (
    <section className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Why Self-Host Your AI Agents?
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Cloud-hosted agents are convenient. But production teams need control, auditability, and agents that learn from their own data.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {reasons.map((reason) => (
            <div
              key={reason.title}
              className="rounded-xl border border-border/60 bg-card p-6"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
                {reason.icon}
              </div>
              <h3 className="text-base font-semibold">{reason.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {reason.copy}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Get Started ── */

function GetStarted() {
  const steps = `# 1. Clone
git clone https://github.com/srinidhis05/agentura.git && cd agentura

# 2. Configure
cp .env.example .env   # add your ANTHROPIC_API_KEY

# 3. Deploy to K8s (K3s / Kind / EKS / GKE)
kubectl apply -f deploy/k8s/operator/

# 4. Copy skills and start building
kubectl cp skills/ executor:/skills/
agentura run dev/app-builder --input '{"description": "build a counter app"}'`;

  return (
    <section id="get-started" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-3xl px-6">
        <div className="mb-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Get Started
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Four commands to a running orchestration engine on any Kubernetes cluster
          </p>
        </div>

        <div className="overflow-hidden rounded-xl border border-border bg-card">
          <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
            <span className="h-3 w-3 rounded-full bg-red-500/60" />
            <span className="h-3 w-3 rounded-full bg-amber-500/60" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/60" />
            <span className="ml-2 text-xs text-muted-foreground">terminal</span>
          </div>
          <pre className="overflow-x-auto p-5 font-mono text-sm leading-relaxed text-muted-foreground">
            <code>{steps}</code>
          </pre>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-4 text-sm">
          <a
            href="https://github.com/srinidhis05/agentura"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg px-5 py-2 font-semibold transition-colors"
            style={{
              backgroundColor: "oklch(0.72 0.17 45)",
              color: "oklch(0.98 0 0)",
            }}
          >
            View on GitHub
          </a>
        </div>
      </div>
    </section>
  );
}

/* ── Footer ── */

function Footer() {
  return (
    <footer className="border-t border-border/50 py-10">
      <div className="mx-auto max-w-6xl px-6">
        <div className="flex flex-col items-center justify-between gap-4 text-xs text-muted-foreground md:flex-row">
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/srinidhis05/agentura"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-foreground"
            >
              GitHub
            </a>
            <span>Apache 2.0</span>
          </div>
          <p className="text-center">
            Self-hostable AI agent orchestration with memory that compounds.
          </p>
        </div>
      </div>
    </footer>
  );
}
