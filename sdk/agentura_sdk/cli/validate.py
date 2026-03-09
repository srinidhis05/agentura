"""agentura validate <domain>/<name> — Validate skill structure and config."""

from pathlib import Path

import click
from rich.console import Console


@click.command()
@click.argument("skill_path")
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default=None,
    help="Root directory for skills.",
)
def validate(skill_path: str, skills_dir: str | None):
    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()
    """Validate a skill's structure and configuration.

    SKILL_PATH should be domain/skill-name, e.g. hr/interview-questions.
    """
    console = Console()

    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name[/]")
        raise SystemExit(1)

    domain, skill_name = parts
    root = Path(skills_dir) / domain / skill_name

    if not root.exists():
        console.print(f"[red]Error: skill not found at {root}[/]")
        raise SystemExit(1)

    errors: list[str] = []
    warnings: list[str] = []

    # Required files
    required = ["SKILL.md", "agentura.config.yaml"]
    for f in required:
        if not (root / f).exists():
            errors.append(f"Missing required file: {f}")

    # Recommended files
    for f in ["DECISIONS.md", "GUARDRAILS.md"]:
        if not (root / f).exists():
            warnings.append(f"Missing recommended file: {f}")

    # Required directories
    for d in ["code", "tests", "fixtures"]:
        if not (root / d).exists():
            warnings.append(f"Missing directory: {d}/")

    # Validate config
    config_raw: dict = {}
    if (root / "agentura.config.yaml").exists():
        from agentura_sdk.runner.config_loader import load_config
        import yaml

        try:
            config = load_config(root / "agentura.config.yaml")
            config_raw = yaml.safe_load((root / "agentura.config.yaml").read_text()) or {}
            if not config.skills:
                warnings.append("No skills defined in agentura.config.yaml")
            if not config.feedback.capture_corrections:
                warnings.append("feedback.capture_corrections is disabled (DEC-006)")
        except Exception as e:
            errors.append(f"Invalid agentura.config.yaml: {e}")

    # Validate mcp_tools format (GR-018)
    mcp_tools = config_raw.get("mcp_tools", [])
    for i, entry in enumerate(mcp_tools):
        if isinstance(entry, str):
            errors.append(
                f"mcp_tools[{i}] is a string ('{entry}') — must be dict "
                f"format: {{server: \"{entry}\", tools: [...]}} (GR-018)"
            )

    # Validate role vs MCP tools consistency
    skill_role = None
    skills_list = config_raw.get("skills", [])
    if skills_list:
        skill_role = skills_list[0].get("role", "specialist")

    # Validate SKILL.md
    skill_md_text = ""
    if (root / "SKILL.md").exists():
        from agentura_sdk.runner.skill_loader import load_skill_md

        try:
            skill = load_skill_md(root / "SKILL.md")
            skill_md_text = (root / "SKILL.md").read_text()
            if skill.metadata.name == "unnamed-skill":
                warnings.append("SKILL.md: skill name is 'unnamed-skill'")
            if len(skill.system_prompt) < 50:
                warnings.append("SKILL.md: prompt is very short (<50 chars)")
        except Exception as e:
            errors.append(f"Invalid SKILL.md: {e}")

    # Check: SKILL.md references MCP tools but role is not agent
    if "mcp__" in skill_md_text and skill_role == "specialist":
        errors.append(
            "SKILL.md references MCP tools (mcp__*) but role is 'specialist'. "
            "MCP tools only work with role: agent + executor: ptc"
        )

    # Check: mcp_tools defined in config but role is not agent
    if mcp_tools and skill_role == "specialist":
        errors.append(
            "mcp_tools defined in config but role is 'specialist'. "
            "Change to role: agent with executor: ptc"
        )

    # Check: role is agent but no agent/executor section
    agent_section = config_raw.get("agent", {}) or config_raw.get("sandbox", {})
    if skill_role == "agent" and not agent_section:
        errors.append(
            "role: agent but no 'agent:' section with 'executor:' specified. "
            "Add agent: {executor: ptc} or agent: {executor: claude-code}"
        )

    # Check: no-follow-up guardrail (GR-019)
    if "NEVER offer follow-up" not in skill_md_text and "NEVER produce a text-only" not in skill_md_text:
        warnings.append(
            "SKILL.md missing no-follow-up guardrail (GR-019). Add: "
            "\"NEVER offer follow-up options like 'Would you like me to...'\""
        )

    # Check for handler
    handler_found = False
    for ext in ["handler.py", "handler.ts", "handler.go"]:
        if (root / "code" / ext).exists():
            handler_found = True
            break
    if not handler_found:
        warnings.append("No handler file in code/ (ok if skill is prompt-only)")

    # Check fixtures
    if not list((root / "fixtures").glob("*.json")) if (root / "fixtures").exists() else True:
        warnings.append("No fixture files in fixtures/")

    # Report
    console.print(f"\n[bold]Validating:[/] {skill_path}\n")

    if errors:
        for e in errors:
            console.print(f"  [red]ERROR[/]   {e}")
    if warnings:
        for w in warnings:
            console.print(f"  [yellow]WARN[/]    {w}")

    if not errors and not warnings:
        console.print("  [green]All checks passed.[/]")
    elif not errors:
        console.print(f"\n  [green]Valid[/] with {len(warnings)} warning(s).")
    else:
        console.print(f"\n  [red]Invalid[/]: {len(errors)} error(s), {len(warnings)} warning(s).")
        raise SystemExit(1)
