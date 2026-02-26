export default function LandingPage() {
  return (
    <div className="min-h-screen text-foreground">
      <Nav />
      <Hero />
      <ProblemSolution />
      <Architecture />
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
          <a href="#features" className="transition-colors hover:text-foreground">Features</a>
          <a href="#architecture" className="transition-colors hover:text-foreground">Architecture</a>
          <a href="#get-started" className="transition-colors hover:text-foreground">Get Started</a>
        </div>

        <a
          href="https://github.com/agentura-ai/agentura"
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
        <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl md:leading-[1.1]">
          Self-Hosted AI Plugins{" "}
          <br className="hidden md:block" />
          for Your Organization
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl">
          Think Claude plugins — but running on your infrastructure, with your data,
          under your control. Domain isolation, policy enforcement, and feedback loops
          that get smarter with every interaction.
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
            href="#architecture"
            className="rounded-lg border border-border px-6 py-2.5 text-sm font-semibold text-muted-foreground transition-colors hover:border-foreground/20 hover:text-foreground"
          >
            View Architecture
          </a>
        </div>
      </div>
    </section>
  );
}

/* ── Problem / Solution Cards ── */

function ProblemSolution() {
  const cards = [
    {
      title: "Security by Default",
      copy: "Domain isolation, RBAC, admission control. Every action bounded, every execution auditable.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
    {
      title: "Skills, Not Code",
      copy: "Domain experts write SKILL.md in Markdown. No Python, no graphs, no code required.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      title: "Learning That Compounds",
      copy: "Corrections auto-generate tests and reflexion rules. After 6 months: 10,000+ regression tests.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
    },
  ];

  return (
    <section id="features" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid gap-6 md:grid-cols-3">
          {cards.map((card) => (
            <div
              key={card.title}
              className="rounded-xl border border-border/60 bg-card p-6"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
                {card.icon}
              </div>
              <h3 className="text-base font-semibold">{card.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {card.copy}
              </p>
            </div>
          ))}
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
            Two-tier control plane: Go gateway for policy, Python executor for skills
          </p>
        </div>

        <div className="mx-auto max-w-5xl space-y-4">
          {/* Top row: User + Operator */}
          <div className="grid gap-4 md:grid-cols-2">
            <ArchBox
              label="User / Chat Client"
              items={["CLI", "Dashboard", "Slack", "API"]}
              borderColor="border-emerald-500/30"
              labelColor="text-emerald-400"
              glow="shadow-emerald-500/5"
            />
            <ArchBox
              label="Operator / SRE"
              items={["agentura CLI", "Dashboard", "Alerts"]}
              borderColor="border-emerald-500/30"
              labelColor="text-emerald-400"
              glow="shadow-emerald-500/5"
            />
          </div>

          {/* Connection line down */}
          <div className="flex justify-center">
            <div className="flex flex-col items-center gap-1">
              <div className="h-6 w-px bg-gradient-to-b from-emerald-500/40 to-blue-500/40" />
              <span className="text-[10px] text-muted-foreground">messages + manage</span>
              <div className="h-6 w-px bg-gradient-to-b from-blue-500/40 to-blue-500/20" />
            </div>
          </div>

          {/* Control Plane */}
          <div className="rounded-xl border border-blue-500/30 bg-blue-500/[0.03] p-5 shadow-lg shadow-blue-500/5">
            <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-blue-400">
              Control Plane &middot; Go Gateway
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              <InnerBox label="API Server" sub="HTTP + WebSocket" color="blue" />
              <InnerBox label="Auth + CORS" sub="Rate Limiting" color="blue" />
              <InnerBox label="Admission Control" sub="Budget + Model Gate" color="blue" />
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
            <div className="grid gap-3 sm:grid-cols-3">
              <InnerBox label="Pydantic AI" sub="Tool Use Loop" color="amber" />
              <InnerBox label="Skill Loader" sub="SKILL.md Parser" color="amber" />
              <InnerBox label="Knowledge Layer" sub="Reflexion + Tests" color="amber" />
            </div>
          </div>

          {/* Connection lines down to three boxes */}
          <div className="flex justify-center">
            <div className="h-8 w-px bg-gradient-to-b from-amber-500/40 to-transparent" />
          </div>

          {/* Horizontal distribution */}
          <div className="mx-auto hidden max-w-3xl md:block">
            <div className="h-px bg-gradient-to-r from-transparent via-muted-foreground/20 to-transparent" />
          </div>

          {/* Bottom row: Skills, MCP Tools, Knowledge */}
          <div className="grid gap-4 md:grid-cols-3">
            <ArchBox
              label="Skills Directory"
              items={["SKILL.md", "Config YAML", "Tests"]}
              borderColor="border-emerald-500/30"
              labelColor="text-emerald-400"
              glow="shadow-emerald-500/5"
            />
            <ArchBox
              label="MCP Tools"
              items={["Slack", "GitHub", "Notion", "DB"]}
              borderColor="border-cyan-500/30"
              labelColor="text-cyan-400"
              glow="shadow-cyan-500/5"
            />
            <ArchBox
              label="Knowledge Layer"
              items={["Reflexions", "Corrections", "Test Suite"]}
              borderColor="border-purple-500/30"
              labelColor="text-purple-400"
              glow="shadow-purple-500/5"
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
  color: "blue" | "amber";
}) {
  const borderMap = { blue: "border-blue-500/20", amber: "border-amber-500/20" };
  return (
    <div className={`rounded-lg border ${borderMap[color]} bg-background/50 px-4 py-3`}>
      <p className="text-sm font-medium">{label}</p>
      <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>
    </div>
  );
}

/* ── Why Self-Host ── */

function WhySelfHost() {
  const reasons = [
    {
      title: "Your Data Never Leaves",
      copy: "Skills run on your infrastructure. Prompts, responses, and domain knowledge stay inside your network. No third-party data processing.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
    },
    {
      title: "Skills That Learn From Your Team",
      copy: "Every correction becomes a regression test. Every test generates a reflexion rule. After 6 months your skills have thousands of guardrails specific to your business.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
    },
    {
      title: "No Vendor Lock-In",
      copy: "Skills are Markdown files. Config is YAML. Swap Claude for GPT, Gemini, or a local model — the skills and knowledge layer stay the same.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      ),
    },
    {
      title: "Domain Isolation Built In",
      copy: "Finance skills can't see HR data. Dev tools can't access production credentials. Each domain has its own RBAC, budget limits, and admission policies.",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
    },
  ];

  return (
    <section className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Why Self-Host Your AI Plugins?
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Cloud plugins are convenient. But enterprises need control, auditability, and skills that learn from their own data.
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
git clone https://github.com/agentura-ai/agentura.git && cd agentura

# 2. Configure
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Launch
docker compose up`;

  return (
    <section id="get-started" className="border-t border-border/50 py-20 md:py-28">
      <div className="mx-auto max-w-3xl px-6">
        <div className="mb-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            Get Started in 60 Seconds
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Three commands. No Kubernetes. No cloud account.
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
            href="https://github.com/agentura-ai/agentura"
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
              href="https://github.com/agentura-ai/agentura"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-foreground"
            >
              GitHub
            </a>
            <span>Apache 2.0</span>
          </div>
          <p className="text-center">
            Built by engineers who believe AI skills should get smarter with every interaction.
          </p>
        </div>
      </div>
    </footer>
  );
}
