export default function LandingPage() {
  return (
    <div className="min-h-screen text-foreground">
      <Nav />
      <Hero />
      <CompoundingIntelligence />
      <AgencySystem />
      <PRFleet />
      <IncubatorPipeline />
      <HowItWorks />
      <ExecutorTypes />
      <Architecture />
      <MemoryLearning />
      <SkillsCatalog />
      <Triggers />
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
          <a href="#how-it-learns" className="transition-colors hover:text-foreground">Features</a>
          <a href="#agency" className="transition-colors hover:text-foreground">Agency</a>
          <a href="#pipelines" className="transition-colors hover:text-foreground">Pipelines</a>
          <a href="#architecture" className="transition-colors hover:text-foreground">Architecture</a>
          <a href="#get-started" className="transition-colors hover:text-foreground">Get Started</a>
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
          28 Skills &middot; 14 Agents &middot; 6 Pipelines &middot; 5 Domains
        </div>

        <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl md:leading-[1.1]">
          Deploy Agent Fleets{" "}
          <br className="hidden md:block" />
          On Your Infrastructure
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl">
          Self-hosted AI agent orchestration for teams that ship.
          PR reviews, feature pipelines, and enterprise workflows &mdash;
          running as parallel fleets on your Kubernetes cluster, learning from every execution.
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
            href="#how-it-learns"
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
              Reflexion rules are automatically injected into future prompts &mdash;
              and with <strong>scoped memory</strong>, learnings propagate across agents.
              A rule learned by your code reviewer is instantly available to your deployer,
              test runner, and every other agent in the same domain.
            </p>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              Six months in, your system has thousands of domain-specific
              learnings that no vendor can replicate &mdash; because they live on
              your infrastructure and belong to your entire organization.
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
              label="Cross-agent learning"
              detail="Scoped memory kicks in. Rules propagate across agents in the same domain. The deployer benefits from what the reviewer learned."
              fill="w-[65%]"
              color="from-blue-500/70 to-cyan-500/40"
            />
            <MoatStep
              week="Month 6+"
              label="Institutional memory"
              detail="Thousands of org-wide guardrails. Auto-synthesis generates new rules from failure patterns. Utility scoring surfaces what works."
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

/* ── Agency System ── */

function AgencySystem() {
  return (
    <section id="agency" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-violet-400">
            Agency System
          </p>
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Agents With Personality and Purpose
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Each agent has a SOUL.md for personality, HEARTBEAT.md for scheduled protocols,
            and agent.yaml for role, budget, and delegation rules
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* SOUL.md */}
          <div className="rounded-xl border border-violet-500/30 bg-card/50 p-6 shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/10 text-violet-400">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold">SOUL.md</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Defines the agent&apos;s personality, communication style, and decision-making philosophy.
              The soul persists across every execution.
            </p>
            <div className="mt-4 overflow-hidden rounded-lg border border-border bg-background/50">
              <div className="flex items-center gap-1.5 border-b border-border px-3 py-1.5">
                <span className="h-2 w-2 rounded-full bg-red-500/50" />
                <span className="h-2 w-2 rounded-full bg-amber-500/50" />
                <span className="h-2 w-2 rounded-full bg-emerald-500/50" />
              </div>
              <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-muted-foreground">
                <code>{`# Operations Lead — Soul

You are the Operations Lead, the
operational brain behind workflow
automation and process optimization.

You think in queues, SLAs, and
resolution patterns. You never guess
when you can measure.

You take ownership of outcomes,
not just assignments.`}</code>
              </pre>
            </div>
          </div>

          {/* HEARTBEAT.md */}
          <div className="rounded-xl border border-violet-500/30 bg-card/50 p-6 shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/10 text-violet-400">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold">HEARTBEAT.md</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Scheduled check-in protocols with cron triggers. Defines what the agent does
              when idle &mdash; polling queues, generating reports, detecting patterns.
            </p>
            <div className="mt-4 overflow-hidden rounded-lg border border-border bg-background/50">
              <div className="flex items-center gap-1.5 border-b border-border px-3 py-1.5">
                <span className="h-2 w-2 rounded-full bg-red-500/50" />
                <span className="h-2 w-2 rounded-full bg-amber-500/50" />
                <span className="h-2 w-2 rounded-full bg-emerald-500/50" />
              </div>
              <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-muted-foreground">
                <code>{`| Cadence   | Action                    |
|-----------|---------------------------|
| Every 15m | Poll queue for new items   |
| Every 1h  | Review SLA breach risk     |
| Daily 8AM | Triage summary + patterns  |
| Weekly    | Resolution metrics report  |

# On SLA warning → escalate
# On pattern (3+ same root cause)
#   → generate systemic fix alert`}</code>
              </pre>
            </div>
          </div>

          {/* agent.yaml */}
          <div className="rounded-xl border border-violet-500/30 bg-card/50 p-6 shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/10 text-violet-400">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold">agent.yaml</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Role, executor type, skills, budget caps, delegation rules, and heartbeat cron schedules.
              All config, zero code.
            </p>
            <div className="mt-4 overflow-hidden rounded-lg border border-border bg-background/50">
              <div className="flex items-center gap-1.5 border-b border-border px-3 py-1.5">
                <span className="h-2 w-2 rounded-full bg-red-500/50" />
                <span className="h-2 w-2 rounded-full bg-amber-500/50" />
                <span className="h-2 w-2 rounded-full bg-emerald-500/50" />
              </div>
              <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-muted-foreground">
                <code>{`name: ecm-manager
role: manager
executor: claude-code
skills:
  - ecm/triage-and-assign
  - ecm/ecm-daily-flow
  - ecm/pattern-intelligence
budget:
  monthly_limit_usd: 50
  per_execution_limit: 0.50
delegation:
  can_assign_to: [ecm-field]
  max_concurrent_tickets: 10`}</code>
              </pre>
            </div>
          </div>
        </div>

        {/* Agent count banner */}
        <div className="mt-10 rounded-xl border border-violet-500/20 bg-violet-500/[0.03] p-6 text-center">
          <p className="text-sm text-muted-foreground">
            <span className="font-semibold text-violet-400">14 agents</span> across 4 domains
            &mdash; Operations, Incubator, Developer Productivity, Project Management &mdash;
            each with personality, scheduled heartbeats, and budget controls
          </p>
        </div>
      </div>
    </section>
  );
}

/* ── PR Fleet ── */

function PRFleet() {
  const agents = [
    {
      name: "Code Reviewer",
      id: "reviewer",
      desc: "Severity-tagged code review with file:line citations. Catches bugs, security issues, and style violations.",
      output: "BLOCKER / WARNING / SUGGESTION",
      color: "blue",
    },
    {
      name: "Test Runner",
      id: "testing",
      desc: "Runs test suite, identifies coverage gaps, and reports untested code paths with evidence.",
      output: "Coverage report + gaps",
      color: "emerald",
    },
    {
      name: "SLT Validator",
      id: "slt",
      desc: "API contract compatibility and breaking change detection. Validates service-level types.",
      output: "Breaking changes list",
      color: "amber",
    },
    {
      name: "Doc Generator",
      id: "docs",
      desc: "Generates CHANGELOG entries, README patches, and inline docstrings for changed code.",
      output: "CHANGELOG + README patch",
      color: "purple",
    },
  ];

  const colorMap = {
    blue: { border: "border-blue-500/30", label: "text-blue-400", tag: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
    emerald: { border: "border-emerald-500/30", label: "text-emerald-400", tag: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    amber: { border: "border-amber-500/30", label: "text-amber-400", tag: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    purple: { border: "border-purple-500/30", label: "text-purple-400", tag: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  };

  return (
    <section id="pr-fleet" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-400">
            Fleet Execution
          </p>
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            4-Agent PR Review Fleet
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            GitHub PR triggers 4 agents in parallel. Results aggregate into a single PR comment.
          </p>
        </div>

        {/* Pipeline diagram — styled components */}
        <div className="mb-10 overflow-hidden rounded-xl border border-blue-500/30 bg-blue-500/[0.03] p-6 md:p-8 shadow-lg">
          <div className="flex flex-col items-center gap-0">
            {/* Trigger */}
            <div className="rounded-lg border border-blue-500/30 bg-background/50 px-6 py-3 text-center">
              <p className="text-sm font-semibold">GitHub PR</p>
              <p className="text-[10px] text-muted-foreground">webhook trigger</p>
            </div>

            {/* Line down */}
            <div className="h-6 w-px bg-gradient-to-b from-blue-500/40 to-blue-500/20" />

            {/* Fan-out label */}
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-blue-400">parallel fan-out</p>

            {/* 4 agents row */}
            <div className="grid w-full gap-3 grid-cols-2 lg:grid-cols-4">
              {[
                { name: "Reviewer", tag: "required", color: "border-blue-500/30 text-blue-400" },
                { name: "Test Runner", tag: "required", color: "border-emerald-500/30 text-emerald-400" },
                { name: "SLT Validator", tag: "optional", color: "border-amber-500/30 text-amber-400" },
                { name: "Doc Generator", tag: "optional", color: "border-purple-500/30 text-purple-400" },
              ].map((a) => (
                <div key={a.name} className={`rounded-lg border ${a.color.split(" ")[0]} bg-background/50 px-4 py-3 text-center`}>
                  <p className={`text-xs font-semibold ${a.color.split(" ")[1]}`}>{a.name}</p>
                  <p className="mt-1 text-[10px] text-muted-foreground">{a.tag}</p>
                </div>
              ))}
            </div>

            {/* Lines converge */}
            <div className="h-6 w-px bg-gradient-to-b from-blue-500/20 to-blue-500/40" />
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-blue-400">fan-in</p>

            {/* Reporter */}
            <div className="rounded-lg border border-blue-500/30 bg-background/50 px-6 py-3 text-center">
              <p className="text-sm font-semibold">PR Reporter</p>
              <p className="text-[10px] text-muted-foreground">aggregates all results</p>
            </div>

            {/* Line down */}
            <div className="h-6 w-px bg-gradient-to-b from-blue-500/40 to-emerald-500/40" />

            {/* Output */}
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/[0.05] px-6 py-3 text-center">
              <p className="text-sm font-semibold text-emerald-400">PR Comment + GitHub Checks</p>
              <p className="text-[10px] text-muted-foreground">one comment, per-agent status checks</p>
            </div>
          </div>
        </div>

        {/* Agent cards */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {agents.map((agent) => {
            const c = colorMap[agent.color as keyof typeof colorMap];
            return (
              <div key={agent.id} className={`rounded-xl border ${c.border} bg-card/50 p-5 shadow-lg`}>
                <h3 className={`text-sm font-semibold ${c.label}`}>{agent.name}</h3>
                <code className={`mt-2 inline-block rounded-md border px-2 py-0.5 text-[10px] font-mono ${c.tag}`}>
                  agent_id: {agent.id}
                </code>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                  {agent.desc}
                </p>
                <p className="mt-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                  Output
                </p>
                <p className="mt-1 text-xs text-muted-foreground">{agent.output}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ── Incubator Pipeline ── */

function IncubatorPipeline() {
  const phases = [
    { name: "Analyze", skill: "spec-analyzer", desc: "Decompose Lovable prototype into backend + mobile specs", color: "text-cyan-400", border: "border-cyan-500/30", bg: "bg-cyan-500/10" },
    { name: "Build", skill: "pit + mobile", desc: "Backend and mobile code generation in parallel", color: "text-emerald-400", border: "border-emerald-500/30", bg: "bg-emerald-500/10" },
    { name: "Refine", skill: "quality-gate", desc: "Clone repos, run builds, verify conventions", color: "text-blue-400", border: "border-blue-500/30", bg: "bg-blue-500/10" },
    { name: "Ship", skill: "preview + merge", desc: "Phone-frame previews and staging merge", color: "text-violet-400", border: "border-violet-500/30", bg: "bg-violet-500/10" },
  ];

  return (
    <section id="pipelines" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-emerald-400">
            Incubator
          </p>
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Prototype to Production Pipeline
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Takes a Lovable prototype and produces PRs in backend and mobile repos
          </p>
        </div>

        {/* Phase flow */}
        <div className="mb-10 grid gap-4 md:grid-cols-4">
          {phases.map((phase, i) => (
            <div key={phase.name} className="flex items-center gap-3">
              <div className={`flex-1 rounded-xl border ${phase.border} bg-card/50 p-5 shadow-lg`}>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`flex h-7 w-7 items-center justify-center rounded-full ${phase.bg} text-xs font-bold ${phase.color}`}>
                    {i + 1}
                  </span>
                  <h3 className={`text-sm font-semibold ${phase.color}`}>{phase.name}</h3>
                </div>
                <code className="block text-[10px] font-mono text-muted-foreground/60 mb-2">{phase.skill}</code>
                <p className="text-xs leading-relaxed text-muted-foreground">{phase.desc}</p>
              </div>
              {i < phases.length - 1 && (
                <span className="hidden text-muted-foreground/30 md:block">&rarr;</span>
              )}
            </div>
          ))}
        </div>

        {/* Pipeline YAML example */}
        <div className="overflow-hidden rounded-xl border border-emerald-500/30 bg-card/50 shadow-lg">
          <div className="flex items-center gap-1.5 border-b border-border px-4 py-2">
            <span className="h-2 w-2 rounded-full bg-red-500/50" />
            <span className="h-2 w-2 rounded-full bg-amber-500/50" />
            <span className="h-2 w-2 rounded-full bg-emerald-500/50" />
            <span className="ml-2 text-[10px] text-muted-foreground">incubator-build.yaml</span>
          </div>
          <pre className="overflow-x-auto p-5 font-mono text-xs leading-relaxed text-muted-foreground">
            <code>{`name: incubator-build
description: "Build backend + mobile from spec"

phases:
  - name: codegen
    type: parallel               # fan-out
    steps:
      - skill: incubator/pit-builder
        agent_id: backend
        required: true
      - skill: incubator/mobile-builder
        agent_id: frontend
        required: true

  - name: verify
    type: sequential
    fan_in_from: codegen          # fan-in
    steps:
      - skill: incubator/quality-gate
        agent_id: reviewer

  - name: report
    type: sequential
    steps:
      - skill: incubator/reporter
        agent_id: reporter`}</code>
          </pre>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            <span className="font-semibold text-emerald-400">7 skills</span> across 4 pipeline phases,{" "}
            <span className="font-semibold text-emerald-400">zero code changes</span> to add a new pipeline
          </p>
        </div>
      </div>
    </section>
  );
}

/* ── How It Works ── */

function HowItWorks() {
  const steps = [
    {
      num: "1",
      title: "Write a Skill",
      desc: "Define your agent in SKILL.md (Markdown) and agentura.config.yaml. Pick an executor type, wire MCP tools, set iteration and token limits.",
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
      desc: "Run one command to correct an agent. The system stores the correction, generates a reflexion rule, and auto-generates regression tests. On the next execution, memory recall injects the reflexion into the prompt automatically.",
      code: `$ agentura correct dev/app-builder \\
    --execution-id EXEC-20260228 \\
    --correction "Always use dark theme"

✓ Correction stored in PostgreSQL
✓ Reflexion generated: "User prefers
  dark mode with purple accent (#8b5cf6)"
✓ Regression test written to
  tests/generated/test_correction_3.py
# Next run auto-recalls this reflexion.`,
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
              <InnerBox label="Rate Limiting" sub="RPS + Burst Control" color="blue" />
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
            Three scopes of memory &mdash; skill, domain, and org &mdash; with cross-agent learning built in
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
              Run <code className="text-xs bg-secondary/80 px-1 py-0.5 rounded">agentura correct</code> to
              submit a correction. The system stores it in PostgreSQL, generates a reflexion rule, and writes
              a DeepEval regression test to <code className="text-xs bg-secondary/80 px-1 py-0.5 rounded">tests/generated/</code>.
              Over time, your skills accumulate domain-specific guardrails.
            </p>
            <div className="mt-4 rounded-lg border border-border bg-background/50 p-3">
              <pre className="font-mono text-xs text-muted-foreground leading-relaxed">{`$ agentura correct dev/app-builder
# Triggers:
#  1. Correction → PostgreSQL
#  2. Reflexion rule → prompt injection
#  3. DeepEval test → tests/generated/
#  4. GUARDRAILS.md → domain guardrails`}</pre>
            </div>
          </div>

          <div className="rounded-xl border border-amber-500/30 bg-card/50 p-6 shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold">Cross-Agent Learning</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Rules have three scopes: <strong>skill</strong>, <strong>domain</strong>, and <strong>org</strong>.
              A reflexion learned by your code reviewer automatically appears for your deployer and test runner.
              Org-level rules apply to every agent. Utility scoring surfaces what actually helps.
            </p>
            <div className="mt-4 rounded-lg border border-border bg-background/50 p-3">
              <pre className="font-mono text-xs text-muted-foreground leading-relaxed">{`# Scoped reflexion injection:
- REFL-042 [skill]: "Check null safety"
- REFL-019 [domain]: "Use Kotlin conventions"
- REFL-003 [org]: "Never expose internal IDs"

# All three injected automatically
# into every dev/* agent's prompt`}</pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Skills Catalog ── */

function SkillsCatalog() {
  const domains = [
    {
      name: "dev",
      label: "Developer Productivity",
      color: "blue",
      skills: [
        { name: "triage", role: "Manager", desc: "Routes dev queries to build/deploy pipeline" },
        { name: "app-builder", role: "Agent", desc: "Builds full-stack web apps from natural language" },
        { name: "deployer", role: "Agent", desc: "Deploys apps to K8s via kubectl MCP" },
        { name: "pr-code-reviewer", role: "Agent", desc: "Severity-tagged code review with file:line citations" },
        { name: "pr-test-runner", role: "Agent", desc: "Runs tests, reports coverage gaps with evidence" },
        { name: "pr-slt-validator", role: "Agent", desc: "API contract compatibility and breaking changes" },
        { name: "pr-doc-generator", role: "Agent", desc: "Generates CHANGELOG, README patches, docstrings" },
        { name: "pr-reporter", role: "Specialist", desc: "Aggregates parallel PR review results" },
      ],
    },
    {
      name: "incubator",
      label: "Feature Incubation",
      color: "emerald",
      skills: [
        { name: "orchestrate", role: "Manager", desc: "Routes to analyze/build/refine/ship pipelines" },
        { name: "spec-analyzer", role: "Specialist", desc: "Decomposes Lovable prototypes into specs" },
        { name: "pit-builder", role: "Agent", desc: "Creates Spring Boot backend module, pushes PR" },
        { name: "mobile-builder", role: "Agent", desc: "Creates Kotlin/Compose feature module, pushes PR" },
        { name: "quality-gate", role: "Agent", desc: "Clones repos, runs builds, checks conventions" },
        { name: "preview-generator", role: "Agent", desc: "Generates phone-frame previews of mobile feature" },
        { name: "reporter", role: "Specialist", desc: "Aggregates pipeline results into PM-facing summary" },
      ],
    },
    {
      name: "operations",
      label: "Operations & Workflows",
      color: "amber",
      skills: [
        { name: "triage", role: "Agent", desc: "Classifies incoming tickets, routes to right queue" },
        { name: "daily-flow", role: "Agent", desc: "Generates daily backlog dashboard with trends" },
        { name: "pattern-intelligence", role: "Agent", desc: "Analyzes recurring patterns, detects SLA breaches" },
        { name: "process-ticket", role: "Agent", desc: "Diagnoses and resolves tickets via MCP tools" },
      ],
    },
  ];

  const colorMap = {
    blue: { border: "border-blue-500/30", label: "text-blue-400", header: "bg-blue-500/10", roleBg: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
    emerald: { border: "border-emerald-500/30", label: "text-emerald-400", header: "bg-emerald-500/10", roleBg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    amber: { border: "border-amber-500/30", label: "text-amber-400", header: "bg-amber-500/10", roleBg: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  };

  const roleColors: Record<string, string> = {
    Manager: "bg-violet-500/10 text-violet-400 border-violet-500/20",
    Agent: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    Specialist: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  };

  return (
    <section id="skills-catalog" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            42 Skills Across 12 Domains
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Each skill is a SKILL.md + config YAML. New skill = new folder, zero code changes.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {domains.map((domain) => {
            const c = colorMap[domain.color as keyof typeof colorMap];
            return (
              <div key={domain.name} className={`rounded-xl border ${c.border} bg-card/50 p-5 shadow-lg`}>
                <div className="mb-4 flex items-center justify-between">
                  <h3 className={`text-sm font-semibold ${c.label}`}>{domain.label}</h3>
                  <code className="text-[10px] font-mono text-muted-foreground/60">{domain.name}/</code>
                </div>
                <div className="space-y-2">
                  {domain.skills.map((skill) => (
                    <div key={skill.name} className="flex items-start gap-2 rounded-lg border border-border/40 bg-background/30 px-3 py-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium truncate">{skill.name}</span>
                          <span className={`shrink-0 rounded-full border px-1.5 py-0 text-[9px] font-medium ${roleColors[skill.role]}`}>
                            {skill.role}
                          </span>
                        </div>
                        <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">{skill.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Additional domains */}
        <div className="mt-6 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {[
            { name: "analytics", label: "Analytics", count: 5 },
            { name: "pm", label: "Project Mgmt", count: 4 },
            { name: "hr", label: "Human Resources", count: 3 },
            { name: "productivity", label: "Productivity", count: 3 },
            { name: "qa", label: "Quality Assurance", count: 1 },
            { name: "support", label: "Support", count: 2 },
          ].map((d) => (
            <div key={d.name} className="rounded-lg border border-border/60 bg-card/50 p-3 text-center">
              <p className="text-xs font-semibold">{d.label}</p>
              <p className="mt-1 text-[10px] text-muted-foreground">{d.count} skills</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Triggers ── */

function Triggers() {
  const triggers = [
    {
      name: "Slack",
      desc: "@mention the bot, DM it, or use /agentura slash commands. Results post back to the channel.",
      config: `# agentura.config.yaml
triggers:
  - type: slack
    command: "/agentura run"`,
      icon: (
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zm10.124 2.521a2.528 2.528 0 0 1 2.52-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.52V8.834zm-1.271 0a2.528 2.528 0 0 1-2.521 2.521 2.528 2.528 0 0 1-2.521-2.521V2.522A2.528 2.528 0 0 1 15.165 0a2.528 2.528 0 0 1 2.522 2.522v6.312zm-2.522 10.124a2.528 2.528 0 0 1 2.522 2.52A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.521-2.522v-2.52h2.521zm0-1.271a2.527 2.527 0 0 1-2.521-2.521 2.528 2.528 0 0 1 2.521-2.522h6.313A2.528 2.528 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.522h-6.313z" />
        </svg>
      ),
      color: "emerald",
    },
    {
      name: "GitHub Webhooks",
      desc: "PR opened or updated triggers the review pipeline. Comments with corrections feed back into the learning loop.",
      config: `# Gateway auto-handles:
# PR opened → dev/pr-reviewer pipeline
# Comment feedback → correction flow
#
# POST /api/v1/webhooks/github`,
      icon: (
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
        </svg>
      ),
      color: "blue",
    },
    {
      name: "Cron Schedules",
      desc: "Run skills on a schedule. The gateway discovers cron triggers from skill configs and manages the schedule automatically.",
      config: `# agentura.config.yaml
triggers:
  - type: cron
    schedule: "0 9 * * 1-5"
    description: "Weekday 9 AM"`,
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: "amber",
    },
    {
      name: "Webhooks + API",
      desc: "Any external system can trigger skills via HMAC-signed webhooks or direct REST API calls. Route through the classifier or target a skill directly.",
      config: `# Generic webhook with HMAC verification
POST /api/v1/channels/{channel}/inbound
X-Webhook-Signature: sha256=...

# Direct skill execution
POST /api/v1/skills/{domain}/{skill}/execute`,
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.12l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
        </svg>
      ),
      color: "purple",
    },
  ];

  const colorMap = {
    emerald: { border: "border-emerald-500/30", icon: "bg-emerald-500/10 text-emerald-400", label: "text-emerald-400" },
    blue: { border: "border-blue-500/30", icon: "bg-blue-500/10 text-blue-400", label: "text-blue-400" },
    amber: { border: "border-amber-500/30", icon: "bg-amber-500/10 text-amber-400", label: "text-amber-400" },
    purple: { border: "border-purple-500/30", icon: "bg-purple-500/10 text-purple-400", label: "text-purple-400" },
  };

  return (
    <section id="triggers" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Trigger From Anywhere
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Skills and pipelines respond to Slack messages, GitHub events, cron schedules, webhooks, or direct API calls
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {triggers.map((trigger) => {
            const c = colorMap[trigger.color as keyof typeof colorMap];
            return (
              <div key={trigger.name} className={`rounded-xl border ${c.border} bg-card/50 p-6 shadow-lg`}>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${c.icon}`}>
                    {trigger.icon}
                  </div>
                  <h3 className={`text-base font-semibold ${c.label}`}>{trigger.name}</h3>
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground mb-4">
                  {trigger.desc}
                </p>
                <div className="overflow-hidden rounded-lg border border-border bg-background/50">
                  <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-muted-foreground">
                    <code>{trigger.config}</code>
                  </pre>
                </div>
              </div>
            );
          })}
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

/* ── Security & Deployment ── */

function WhySelfHost() {
  const security = [
    {
      title: "HMAC Webhook Verification",
      desc: "Inbound webhooks (GitHub, Slack, custom) are verified via SHA-256 HMAC signatures before processing.",
      status: "built",
    },
    {
      title: "JWT + Domain-Scoped RBAC",
      desc: "Gateway validates JWTs and extracts domain_scope claims. Skills can only be executed within authorized domains.",
      status: "built",
    },
    {
      title: "Ephemeral Agent Pods",
      desc: "Each execution creates an isolated K8s pod with bounded CPU/memory. Pod is destroyed after completion — no persistent attack surface.",
      status: "built",
    },
    {
      title: "Rate Limiting",
      desc: "Global RPS and burst control at the gateway layer. Configurable per deployment.",
      status: "built",
    },
    {
      title: "Scoped MCP Tool Bindings",
      desc: "Each skill declares which MCP tools it can access. Dev skills get kubectl; HR skills get different tools. No skill has blanket access.",
      status: "built",
    },
    {
      title: "Memory Governance",
      desc: "ACL-aware recall, PII scanning, retention/TTL, and audit trails for enterprise compliance.",
      status: "roadmap",
    },
  ];

  const deployment = [
    {
      title: "Any Kubernetes Cluster",
      desc: "K3s on a Raspberry Pi, Kind for dev, EKS/GKE/AKS for production. Same manifests, same behavior.",
    },
    {
      title: "VPC-Only Egress",
      desc: "All data stays in your cluster. Only model API calls (Anthropic/OpenRouter) leave your network — and those can be routed through a proxy.",
    },
    {
      title: "Multi-Model via OpenRouter",
      desc: "Swap between Claude, GPT-4o, Gemini, DeepSeek, or Llama without changing skills. One API key, 200+ models.",
    },
    {
      title: "Local Model Support",
      desc: "Ollama and vLLM integration for fully air-gapped deployments where no data leaves the network.",
      status: "roadmap",
    },
  ];

  return (
    <>
      {/* Security */}
      <section id="security" className="border-t border-border/50 py-20 md:py-28">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
              Security by Default
            </h2>
            <p className="mt-3 text-sm text-muted-foreground">
              Built for teams where security review is a gate, not an afterthought
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {security.map((item) => (
              <div key={item.title} className="rounded-xl border border-border/60 bg-card/50 p-5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-semibold">{item.title}</h3>
                  {item.status === "roadmap" ? (
                    <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400">
                      Roadmap
                    </span>
                  ) : (
                    <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
                      Built
                    </span>
                  )}
                </div>
                <p className="text-xs leading-relaxed text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Deployment */}
      <section className="border-t border-border/50 py-20 md:py-28">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
              Runs Where You Need It
            </h2>
            <p className="mt-3 text-sm text-muted-foreground">
              From a single-node K3s cluster to managed Kubernetes in any cloud
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {deployment.map((item) => (
              <div key={item.title} className="rounded-xl border border-border/60 bg-card p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-semibold">{item.title}</h3>
                  {"status" in item && item.status === "roadmap" && (
                    <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400">
                      Roadmap
                    </span>
                  )}
                </div>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
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
