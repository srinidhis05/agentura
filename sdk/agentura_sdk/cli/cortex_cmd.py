"""agentura cortex — PM interview-driven skill creation.

Three-phase flow:
1. Interview (Haiku) — conversational PM questions to understand the problem
2. Generation (Sonnet) — produces SKILL.md from interview spec
3. Refinement (Sonnet) — review loop until user approves

Falls back to legacy wizard via --quick or when no API key is set.
"""

import json
import logging
import os
import re
from datetime import date
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()
logger = logging.getLogger(__name__)

# Model IDs per provider
_MODELS = {
    "openrouter": {
        "haiku": "anthropic/claude-haiku-4.5",
        "sonnet": "anthropic/claude-sonnet-4-5-20250929",
    },
    "anthropic": {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-5-20250929",
    },
}

_MAX_INTERVIEW_TURNS = 10
_MAX_REFINE_TURNS = 5


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------

def _get_provider() -> str | None:
    """Return 'openrouter', 'anthropic', or None."""
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def _llm_call(
    provider: str,
    model_tier: str,
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Unified multi-turn LLM call. Returns assistant content string."""
    if provider == "openrouter":
        from agentura_sdk.runner.openrouter import chat_completion_messages
        resp = chat_completion_messages(
            model=_MODELS["openrouter"][model_tier],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.content
    else:
        import anthropic
        # Separate system message from conversation messages
        system_text = ""
        conv_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                conv_messages.append(msg)

        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=_MODELS["anthropic"][model_tier],
            max_tokens=max_tokens,
            system=system_text,
            messages=conv_messages,
            temperature=temperature,
        )
        return resp.content[0].text


# ---------------------------------------------------------------------------
# Skills context gathering
# ---------------------------------------------------------------------------

def _gather_skills_context(skills_dir: Path) -> str:
    """Scan skills/ to build context for the interview LLM.

    Returns a markdown string listing domains, skills, and example excerpts.
    """
    if not skills_dir.exists():
        return "No existing skills found."

    lines = ["## Existing Skills\n"]
    example_excerpts: list[str] = []
    examples_collected = 0

    for domain_dir in sorted(skills_dir.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("."):
            continue

        skill_names = []
        for skill_dir in sorted(domain_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_md.exists():
                continue

            # Extract role from frontmatter
            role = _extract_frontmatter_field(skill_md, "role") or "?"
            skill_names.append(f"  - {skill_dir.name} ({role})")

            # Collect up to 2 example excerpts
            if examples_collected < 2:
                excerpt = _truncate_skill_md(skill_md, max_lines=60)
                example_excerpts.append(
                    f"### Example: {domain_dir.name}/{skill_dir.name}\n```\n{excerpt}\n```"
                )
                examples_collected += 1

        if skill_names:
            # Include DOMAIN.md summary if it exists
            domain_md = domain_dir / "DOMAIN.md"
            domain_hint = ""
            if domain_md.exists():
                first_lines = domain_md.read_text().split("\n")[:3]
                domain_hint = f" — {' '.join(first_lines).strip()[:100]}"

            lines.append(f"### {domain_dir.name}{domain_hint}")
            lines.extend(skill_names)
            lines.append("")

    if example_excerpts:
        lines.append("\n## Example SKILL.md Files\n")
        lines.extend(example_excerpts)

    return "\n".join(lines)


def _extract_frontmatter_field(skill_md: Path, field: str) -> str | None:
    """Quick extraction of a single frontmatter field without full parsing."""
    try:
        text = skill_md.read_text(errors="replace")
    except OSError:
        return None

    if not text.startswith("---"):
        return None

    end = text.find("---", 3)
    if end == -1:
        return None

    frontmatter = text[3:end]
    for line in frontmatter.split("\n"):
        if line.strip().startswith(f"{field}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def _truncate_skill_md(skill_md: Path, max_lines: int = 60) -> str:
    """Return first N lines of a SKILL.md for example context."""
    try:
        lines = skill_md.read_text(errors="replace").split("\n")[:max_lines]
        return "\n".join(lines)
    except OSError:
        return ""


def _load_domain_md_for_context(skills_dir: Path, domain: str) -> str:
    """Load DOMAIN.md for a specific domain, if it exists."""
    domain_md = skills_dir / domain / "DOMAIN.md"
    if domain_md.exists():
        return domain_md.read_text().strip()
    return ""


# ---------------------------------------------------------------------------
# Skill-based prompt loading
# ---------------------------------------------------------------------------

def _load_cortex_skill(skills_dir: Path, skill_name: str) -> str | None:
    """Load a platform cortex skill via the standard skill loader pipeline.

    Composes: WORKSPACE + DOMAIN + REFLEXION + SKILL body.
    Returns the composed prompt string, or None if loading fails.
    """
    skill_path = skills_dir / "platform" / skill_name / "SKILL.md"
    if not skill_path.exists():
        return None

    try:
        from agentura_sdk.runner.skill_loader import load_skill_md
        loaded = load_skill_md(skill_path, include_reflexions=True)
        parts = [p for p in [
            loaded.workspace_context,
            loaded.domain_context,
            loaded.reflexion_context,
            loaded.system_prompt,
        ] if p]
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        logger.debug("Failed to load cortex skill %s: %s", skill_name, e)
        return None


# ---------------------------------------------------------------------------
# Phase 1: Interview
# ---------------------------------------------------------------------------

_FALLBACK_INTERVIEW_PROMPT = """You are a senior product manager conducting a discovery interview to define a new AI skill.

Your goal: understand the BUSINESS PROBLEM, then infer the technical specification.

## Interview Style
- Ask ONE question at a time
- Start with "What problem are you trying to solve?"
- Then ask about: who uses it, what they expect, what data exists, what should never happen
- Be conversational and brief — no walls of text
- After 3-5 questions, when you have enough context, output the spec

## Existing Skills Context
{skills_context}

{domain_context}

## Completion Signal
When you have enough information (usually after 3-5 questions), output a JSON spec block:

```json
{{
  "domain": "the-domain",
  "skill_name": "kebab-case-name",
  "role": "specialist|manager|field",
  "model": "anthropic/claude-sonnet-4.5",
  "description": "One sentence description",
  "input_fields": ["field1", "field2"],
  "output_fields": ["field1", "field2"],
  "guardrails": ["rule1", "rule2"],
  "trigger": "manual",
  "routes_to": [],
  "interview_notes": "Key insights from the conversation"
}}
```

Choose the domain from existing domains when it fits. Suggest a new domain only when nothing existing applies.
For role: "field" = data collection via tools, "specialist" = deep domain processing, "manager" = orchestrates other skills.
For model: use sonnet for complex reasoning, haiku for simple/fast tasks."""


def _build_interview_system_prompt(skills_dir: Path) -> str:
    """Build the interview system prompt with skills context injected.

    Tries to load the cortex-interviewer skill first; falls back to embedded prompt.
    """
    skills_context = _gather_skills_context(skills_dir)
    loaded = _load_cortex_skill(skills_dir, "cortex-interviewer")
    if loaded:
        return loaded.format(skills_context=skills_context, domain_context="")
    return _FALLBACK_INTERVIEW_PROMPT.format(
        skills_context=skills_context,
        domain_context="",
    )


def _parse_interview_spec(response: str) -> dict | None:
    """Extract JSON spec block from LLM response. Returns None if still interviewing."""
    match = re.search(r"```json\s*\n(\{.*?\})\s*\n```", response, re.DOTALL)
    if not match:
        return None
    try:
        spec = json.loads(match.group(1))
        # Validate required fields
        required = {"domain", "skill_name", "role", "description"}
        if required.issubset(spec.keys()):
            return spec
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def _run_interview(provider: str, skills_dir: Path) -> dict | None:
    """Phase 1: Conversational PM interview. Returns spec dict or None on failure."""
    system_prompt = _build_interview_system_prompt(skills_dir)
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # Kick off the conversation
    messages.append({"role": "user", "content": "I want to create a new skill."})

    for turn in range(_MAX_INTERVIEW_TURNS):
        try:
            response = _llm_call(provider, "haiku", messages)
        except Exception as e:
            console.print(f"\n[yellow]Interview error: {e}[/]")
            return None

        messages.append({"role": "assistant", "content": response})

        # Check if the LLM produced a spec
        spec = _parse_interview_spec(response)
        if spec:
            # Show the final message (may contain the spec + explanation)
            display_text = re.sub(
                r"```json\s*\n\{.*?\}\s*\n```", "", response, flags=re.DOTALL
            ).strip()
            if display_text:
                console.print(f"\n[bold cyan]Cortex:[/] {display_text}")
            return spec

        # Display LLM question and get user answer
        console.print(f"\n[bold cyan]Cortex:[/] {response}")
        user_input = Prompt.ask("\n[bold]You[/]")

        if user_input.lower() in ("quit", "exit", "q"):
            return None

        messages.append({"role": "user", "content": user_input})

        # After the LLM suggests a domain, inject domain context
        if turn == 2:
            domain_guess = _guess_domain_from_messages(messages)
            if domain_guess:
                domain_ctx = _load_domain_md_for_context(skills_dir, domain_guess)
                if domain_ctx:
                    messages.append({
                        "role": "system",
                        "content": f"## Target Domain Context\n{domain_ctx}",
                    })

    console.print("[yellow]Interview reached turn limit.[/]")
    return None


def _guess_domain_from_messages(messages: list[dict]) -> str | None:
    """Try to extract a domain name mentioned in assistant messages."""
    for msg in reversed(messages):
        if msg["role"] != "assistant":
            continue
        # Look for domain mentions like "ecm", "frm", "hr", "wealth", "platform"
        for domain in ("ecm", "frm", "hr", "wealth", "platform"):
            if domain in msg["content"].lower():
                return domain
    return None


# ---------------------------------------------------------------------------
# Phase 2: Generation
# ---------------------------------------------------------------------------

_FALLBACK_GENERATION_PROMPT = """You are an expert at writing Agentura SKILL.md files. Generate a complete SKILL.md.

## Required Format

The file MUST start with YAML frontmatter (between --- delimiters) containing:
- name, role, domain, trigger, model, cost_budget_per_execution, timeout

Then include these markdown sections:
- # [Skill Title] (one-line description after title)
- ## Task (what the skill does, 2-3 paragraphs)
- ## Context You'll Receive (input fields as bullet list with types)
- ## Output Format (expected output structure with example)
- ## Guardrails (domain-specific rules as bullet list)
- ## Routes To (downstream skills, or "None — terminal skill")

## Style
- Be specific and practical — no placeholder text
- Use the same voice and density as examples below
- Guardrails should be real constraints, not generic advice

{skills_context}"""


def _generate_skill_md(provider: str, spec: dict, skills_dir: Path) -> str:
    """Phase 2: Generate SKILL.md from interview spec using Sonnet."""
    skills_context = _gather_skills_context(skills_dir)
    loaded = _load_cortex_skill(skills_dir, "cortex-generator")
    if loaded:
        system = loaded.format(skills_context=skills_context)
    else:
        system = _FALLBACK_GENERATION_PROMPT.format(skills_context=skills_context)

    user_msg = f"""Create a SKILL.md from this interview spec:

```json
{json.dumps(spec, indent=2)}
```

Interview notes: {spec.get('interview_notes', 'N/A')}"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]

    return _llm_call(provider, "sonnet", messages, temperature=0.2)


# ---------------------------------------------------------------------------
# Phase 3: Refinement
# ---------------------------------------------------------------------------

_FALLBACK_REFINER_PROMPT = (
    "You are refining a SKILL.md based on user feedback. "
    "Return the COMPLETE updated SKILL.md — not a diff.\n\n"
    "{skills_context}"
)


def _review_loop(provider: str, draft: str, skills_dir: Path) -> str:
    """Phase 3: Show draft, collect feedback, refine until approved."""
    skills_context = _gather_skills_context(skills_dir)
    loaded = _load_cortex_skill(skills_dir, "cortex-refiner")
    if loaded:
        refine_system = loaded.format(skills_context=skills_context)
    else:
        refine_system = _FALLBACK_REFINER_PROMPT.format(skills_context=skills_context)
    current = draft

    for _ in range(_MAX_REFINE_TURNS):
        console.print()
        console.print(Panel(
            Markdown(current),
            title="[bold]Generated SKILL.md[/]",
            border_style="green",
            padding=(1, 2),
        ))

        feedback = Prompt.ask(
            "\n[bold]What would you change?[/] (enter to approve)",
            default="approve",
        )

        if feedback.lower() in ("approve", "lgtm", "ok", "good", "yes", ""):
            return current

        # Refine via Sonnet
        messages = [
            {"role": "system", "content": refine_system},
            {"role": "user", "content": f"Current SKILL.md:\n\n{current}"},
            {"role": "assistant", "content": "What changes would you like?"},
            {"role": "user", "content": feedback},
        ]

        try:
            current = _llm_call(provider, "sonnet", messages, temperature=0.2)
            console.print("[dim]Revised.[/]")
        except Exception as e:
            console.print(f"[yellow]Refinement failed: {e}. Keeping current draft.[/]")
            return current

    return current


# ---------------------------------------------------------------------------
# File creation (shared by both paths)
# ---------------------------------------------------------------------------

def _create_skill_files(
    skills_dir: Path,
    domain: str,
    skill_name: str,
    skill_md_content: str,
    description: str,
    input_fields: str,
    role: str,
    model: str,
    lang: str = "python",
    mcp_tools: list[str] | None = None,
) -> Path:
    """Create all skill files: SKILL.md, config, handler, tests, fixtures."""
    root = Path(skills_dir) / domain / skill_name

    # Create directories
    for d in [root, root / "code", root / "tests", root / "fixtures"]:
        d.mkdir(parents=True, exist_ok=True)

    # Domain-level files (if new domain)
    domain_root = Path(skills_dir) / domain
    if not (domain_root / "DOMAIN.md").exists():
        from jinja2 import Environment, PackageLoader
        env = Environment(
            loader=PackageLoader("agentura_sdk", "templates"),
            keep_trailing_newline=True,
        )
        ctx = {
            "domain": domain, "skill_name": skill_name,
            "role": role, "lang": lang, "date": date.today().isoformat(),
        }
        for filepath, tmpl in [
            (domain_root / "DOMAIN.md", "domain.md.j2"),
            (domain_root / "DECISIONS.md", "decisions.md.j2"),
            (domain_root / "GUARDRAILS.md", "guardrails.md.j2"),
        ]:
            filepath.write_text(env.get_template(tmpl).render(**ctx))
        console.print(f"  [green]+[/] Domain files for [cyan]{domain}[/]")

    # SKILL.md
    (root / "SKILL.md").write_text(skill_md_content)
    console.print("  [green]+[/] SKILL.md")

    # Config
    mcp_section = ""
    if mcp_tools:
        mcp_lines = "\n".join(
            f'  - server: {t}\n    tools: ["query"]' for t in mcp_tools
        )
        mcp_section = f"\nmcp_tools:\n{mcp_lines}\n"

    config_content = f"""domain:
  name: {domain}
  description: "{description[:80]}"

skills:
  - name: {skill_name}
    role: {role}
    model: {model}
    trigger: manual
    cost_budget: "$0.10"
    timeout: "30s"
{mcp_section}
guardrails:
  max_cost_per_execution: "$0.50"
  human_in_loop:
    require_approval: false
"""
    (root / "agentura.config.yaml").write_text(config_content)
    console.print("  [green]+[/] agentura.config.yaml")

    # Handler + tests via Jinja2
    from jinja2 import Environment, PackageLoader
    env = Environment(
        loader=PackageLoader("agentura_sdk", "templates"),
        keep_trailing_newline=True,
    )
    handler_ext = {"python": "handler.py", "typescript": "handler.ts", "go": "handler.go"}
    handler_file = handler_ext[lang]
    ctx = {
        "domain": domain, "skill_name": skill_name,
        "role": role, "lang": lang, "date": date.today().isoformat(),
    }
    (root / "code" / handler_file).write_text(
        env.get_template(f"{handler_file}.j2").render(**ctx)
    )
    console.print(f"  [green]+[/] code/{handler_file}")

    for test_file, test_tmpl in [
        ("tests/test_deepeval.py", "test_deepeval.py.j2"),
        ("tests/test_promptfoo.yaml", "test_promptfoo.yaml.j2"),
    ]:
        (root / test_file).write_text(env.get_template(test_tmpl).render(**ctx))
    console.print("  [green]+[/] tests/test_deepeval.py + test_promptfoo.yaml")

    # Fixture
    console.print("  [dim]Generating fixture...[/]")
    fixture = _generate_fixture_via_llm(description, input_fields)
    if fixture:
        (root / "fixtures" / "sample_input.json").write_text(
            json.dumps(fixture, indent=2)
        )
        console.print("  [green]+[/] fixtures/sample_input.json [dim](AI-generated)[/]")
    else:
        fields = [f.strip() for f in input_fields.split(",")]
        default_fixture = {f: f"sample_{f}" for f in fields}
        (root / "fixtures" / "sample_input.json").write_text(
            json.dumps(default_fixture, indent=2)
        )
        console.print("  [green]+[/] fixtures/sample_input.json [dim](default)[/]")

    return root


# ---------------------------------------------------------------------------
# Fixture generation (unchanged)
# ---------------------------------------------------------------------------

def _generate_fixture_via_llm(description: str, input_fields: str) -> dict | None:
    """Generate a realistic sample_input.json fixture."""
    provider = _get_provider()
    if not provider:
        return None

    prompt = f"""Generate a realistic JSON input fixture for an AI skill.
Skill: {description}
Expected input fields: {input_fields}

Return ONLY valid JSON (no markdown, no explanation). Include realistic sample values."""

    try:
        messages = [
            {"role": "system", "content": "Return only valid JSON. No markdown."},
            {"role": "user", "content": prompt},
        ]
        content = _llm_call(provider, "haiku", messages, max_tokens=500)
        return json.loads(content)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Legacy wizard (preserved for --quick)
# ---------------------------------------------------------------------------

def _legacy_wizard(skills_dir: str):
    """Original 8-step wizard — accessible via --quick or when no API key."""
    console.print(Panel(
        "[bold cyan]Agentura Cortex[/] — Quick Skill Creator\n\n"
        "Answer a few questions to scaffold a new skill.",
        title="Cortex (Quick Mode)",
        border_style="cyan",
    ))

    # Step 1: Domain and name
    console.print("\n[bold]Step 1:[/] Identity")
    domain = Prompt.ask("  Domain", default="ecm")
    skill_name = Prompt.ask("  Skill name", default="new-skill")

    skill_path = f"{domain}/{skill_name}"
    root = Path(skills_dir) / domain / skill_name

    if root.exists():
        console.print(f"[red]Skill already exists: {root}[/]")
        raise SystemExit(1)

    # Step 2: What does it do?
    console.print("\n[bold]Step 2:[/] Purpose")
    description = Prompt.ask("  What should this skill do? (1-2 sentences)")

    # Step 3: Role
    console.print("\n[bold]Step 3:[/] Role")
    console.print("  [dim]manager[/]     — routes to other skills, orchestrates workflows")
    console.print("  [dim]specialist[/]  — deep domain expertise, executes tasks")
    console.print("  [dim]field[/]       — data collection via MCP tools")
    role = Prompt.ask(
        "  Role", choices=["manager", "specialist", "field"], default="specialist",
    )

    # Step 4: I/O Schema
    console.print("\n[bold]Step 4:[/] Input/Output")
    input_fields = Prompt.ask(
        "  What input does it receive? (comma-separated fields)",
        default="query, context",
    )
    output_fields = Prompt.ask(
        "  What should it output? (comma-separated fields)",
        default="answer, confidence, reasoning",
    )

    # Step 5: Guardrails
    console.print("\n[bold]Step 5:[/] Guardrails")
    guardrails = Prompt.ask(
        "  Any rules or constraints? (comma-separated, or 'none')",
        default="none",
    )

    # Step 6: Model
    console.print("\n[bold]Step 6:[/] Model")
    model = Prompt.ask(
        "  LLM model",
        default="anthropic/claude-sonnet-4-5-20250929",
    )

    # Step 7: Language
    lang = Prompt.ask(
        "  Handler language", choices=["python", "typescript", "go"], default="python",
    )

    # Step 8: MCP tools
    console.print("\n[bold]Step 7:[/] MCP Tools")
    mcp_tools_str = Prompt.ask(
        "  MCP tool servers needed? (comma-separated, or 'none')",
        default="none",
    )
    mcp_tools = (
        [] if mcp_tools_str == "none"
        else [t.strip() for t in mcp_tools_str.split(",")]
    )

    # Confirm
    console.print("\n" + "─" * 50)
    console.print(f"  [cyan]Skill:[/]       {skill_path}")
    console.print(f"  [cyan]Role:[/]        {role}")
    console.print(f"  [cyan]Model:[/]       {model}")
    console.print(f"  [cyan]Description:[/] {description}")
    console.print(f"  [cyan]Input:[/]       {input_fields}")
    console.print(f"  [cyan]Output:[/]      {output_fields}")
    if mcp_tools:
        console.print(f"  [cyan]MCP Tools:[/]  {', '.join(mcp_tools)}")
    console.print("─" * 50)

    if not Confirm.ask("\n  Create this skill?", default=True):
        console.print("[yellow]Cancelled.[/]")
        return

    # Generate SKILL.md via LLM
    console.print("\n[bold]Creating skill...[/]")
    console.print("  [dim]Generating SKILL.md via LLM...[/]")

    provider = _get_provider()
    skill_md_content = None
    if provider:
        system = """You are an expert at writing Agentura SKILL.md files. Generate a complete SKILL.md file.

The file MUST start with a YAML frontmatter block (between --- delimiters) containing:
- name, role, domain, trigger, model, cost_budget_per_execution, timeout

Then include markdown sections:
- # [Skill Title] (one-line description)
- ## Task (what the skill does, 2-3 paragraphs)
- ## Context You'll Receive (input fields as bullet list with types)
- ## Output Format (expected JSON output structure)
- ## Guardrails (domain-specific rules as bullet list)
- ## Routes To (downstream skills, or "None — terminal skill" if standalone)

Be specific and practical. Use the user's description to create real, useful content."""

        user_msg = f"""Create a SKILL.md for:
- Domain: {domain}
- Skill name: {skill_name}
- Role: {role}
- Model: {model}
- Description: {description}
- Input fields: {input_fields}
- Output fields: {output_fields}
- Guardrails/rules: {guardrails}"""

        try:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ]
            skill_md_content = _llm_call(provider, "haiku", messages)
        except Exception as e:
            console.print(
                f"[yellow]LLM generation failed: {e}. Using template fallback.[/]"
            )

    if not skill_md_content:
        from jinja2 import Environment, PackageLoader
        env = Environment(
            loader=PackageLoader("agentura_sdk", "templates"),
            keep_trailing_newline=True,
        )
        ctx = {
            "domain": domain, "skill_name": skill_name,
            "role": role, "lang": lang, "date": date.today().isoformat(),
        }
        skill_md_content = env.get_template("skill.md.j2").render(**ctx)
        skill_md_content = skill_md_content.replace(
            "[What this skill does in one sentence]", description,
        )
        console.print("  [dim](using template fallback)[/]")

    root = _create_skill_files(
        skills_dir=skills_dir,
        domain=domain,
        skill_name=skill_name,
        skill_md_content=skill_md_content,
        description=description,
        input_fields=input_fields,
        role=role,
        model=model,
        lang=lang,
        mcp_tools=mcp_tools,
    )

    _print_next_steps(root, skill_path)


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

@click.command("cortex")
@click.option("--skills-dir", type=click.Path(), default=None, help="Root skills directory.")
@click.option("--quick", is_flag=True, help="Use legacy step-by-step wizard.")
def cortex(skills_dir: str | None, quick: bool):
    """Interactive skill creation wizard — describe what you want, get a working skill."""
    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()

    provider = _get_provider()

    # Graceful degradation: no API key → legacy wizard
    if quick or not provider:
        if not provider and not quick:
            console.print(
                "[yellow]No API key found (ANTHROPIC_API_KEY or OPENROUTER_API_KEY). "
                "Falling back to quick mode.[/]\n"
            )
        _legacy_wizard(skills_dir)
        return

    # PM Interview flow
    console.print(Panel(
        "[bold cyan]Agentura Cortex[/] — AI Skill Creator\n\n"
        "I'll interview you about the problem you're solving,\n"
        "then generate a production-ready skill.\n\n"
        "[dim]Type 'quit' to exit. Use --quick for the step-by-step wizard.[/]",
        title="Cortex",
        border_style="cyan",
    ))

    skills_path = Path(skills_dir)

    # Phase 1: Interview
    console.print("\n[bold]Phase 1:[/] Discovery Interview\n")
    spec = _run_interview(provider, skills_path)

    if not spec:
        if Confirm.ask("\nSwitch to quick mode?", default=True):
            _legacy_wizard(skills_dir)
        return

    # Show inferred spec
    console.print("\n" + "─" * 50)
    console.print("[bold]Inferred specification:[/]")
    console.print(f"  [cyan]Domain:[/]      {spec.get('domain', '?')}")
    console.print(f"  [cyan]Skill:[/]       {spec.get('skill_name', '?')}")
    console.print(f"  [cyan]Role:[/]        {spec.get('role', '?')}")
    console.print(f"  [cyan]Model:[/]       {spec.get('model', '?')}")
    console.print(f"  [cyan]Description:[/] {spec.get('description', '?')}")
    console.print("─" * 50)

    # Check if skill already exists
    root = skills_path / spec["domain"] / spec["skill_name"]
    if root.exists():
        console.print(f"\n[red]Skill already exists: {root}[/]")
        raise SystemExit(1)

    if not Confirm.ask("\nProceed with generation?", default=True):
        console.print("[yellow]Cancelled.[/]")
        return

    # Phase 2: Generation
    console.print("\n[bold]Phase 2:[/] Generating SKILL.md...\n")
    try:
        draft = _generate_skill_md(provider, spec, skills_path)
    except Exception as e:
        console.print(f"[yellow]Generation failed: {e}[/]")
        console.print("[dim]Falling back to template...[/]")
        from jinja2 import Environment, PackageLoader
        env = Environment(
            loader=PackageLoader("agentura_sdk", "templates"),
            keep_trailing_newline=True,
        )
        ctx = {
            "domain": spec["domain"], "skill_name": spec["skill_name"],
            "role": spec.get("role", "specialist"), "lang": "python",
            "date": date.today().isoformat(),
        }
        draft = env.get_template("skill.md.j2").render(**ctx)

    # Phase 3: Refinement
    console.print("\n[bold]Phase 3:[/] Review & Refine")
    final_md = _review_loop(provider, draft, skills_path)

    # Language selection (only thing we can't infer)
    lang = Prompt.ask(
        "\n  Handler language", choices=["python", "typescript", "go"], default="python",
    )

    # Create files
    console.print("\n[bold]Creating skill files...[/]")
    input_fields_str = ", ".join(spec.get("input_fields", ["query", "context"]))
    skill_root = _create_skill_files(
        skills_dir=skills_dir,
        domain=spec["domain"],
        skill_name=spec["skill_name"],
        skill_md_content=final_md,
        description=spec.get("description", ""),
        input_fields=input_fields_str,
        role=spec.get("role", "specialist"),
        model=spec.get("model", "anthropic/claude-sonnet-4-5-20250929"),
        lang=lang,
        mcp_tools=None,
    )

    skill_path = f"{spec['domain']}/{spec['skill_name']}"
    _print_next_steps(skill_root, skill_path)


def _print_next_steps(root: Path, skill_path: str):
    """Print post-creation instructions."""
    console.print(f"\n[green bold]Skill created:[/] {root}\n")
    console.print("[cyan]Next steps:[/]")
    console.print(f"  1. Review {root}/SKILL.md")
    console.print(f"  2. agentura validate {skill_path}")
    console.print(f"  3. agentura run {skill_path} --dry-run")
    console.print(f"  4. agentura run {skill_path}")
    console.print(f"  5. agentura test {skill_path}")
