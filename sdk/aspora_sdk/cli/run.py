"""aspora run <domain>/<name> — Execute a skill locally via Pydantic AI."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel


@click.command()
@click.argument("skill_path")
@click.option("--input", "input_file", type=click.Path(exists=True), help="JSON input file.")
@click.option("--dry-run", is_flag=True, help="Validate without calling model.")
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default="skills",
    help="Root directory for skills.",
)
@click.option("--model", "model_override", help="Override model from config.")
def run(skill_path: str, input_file: str | None, dry_run: bool, skills_dir: str, model_override: str | None):
    """Run a skill locally.

    SKILL_PATH should be domain/skill-name, e.g. wealth/suggest-allocation.
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

    # Load config and skill
    from aspora_sdk.runner.config_loader import load_config
    from aspora_sdk.runner.skill_loader import load_skill_md
    from aspora_sdk.types import SkillContext

    config = load_config(root / "aspora.config.yaml")
    skill_md = load_skill_md(root / "SKILL.md")

    # Build input data
    input_data = {}
    if input_file:
        input_data = json.loads(Path(input_file).read_text())
    elif (root / "fixtures" / "sample_input.json").exists():
        input_data = json.loads((root / "fixtures" / "sample_input.json").read_text())
        console.print("[dim]Using fixtures/sample_input.json (no --input specified)[/]")

    model = model_override or skill_md.metadata.model

    # Compose system prompt: DOMAIN.md (identity/voice) + Reflexion (learned rules) + SKILL.md (task)
    prompt_parts = []
    if skill_md.domain_context:
        prompt_parts.append(skill_md.domain_context)
    if skill_md.reflexion_context:
        prompt_parts.append(skill_md.reflexion_context)
    prompt_parts.append(skill_md.system_prompt)
    composed_prompt = "\n\n---\n\n".join(prompt_parts)

    ctx = SkillContext(
        skill_name=skill_md.metadata.name,
        domain=skill_md.metadata.domain,
        role=skill_md.metadata.role,
        model=model,
        system_prompt=composed_prompt,
        input_data=input_data,
    )

    if dry_run:
        console.print(Panel("[yellow]DRY RUN[/] — Validating without calling model"))
        console.print(f"  Skill: {ctx.skill_name}")
        console.print(f"  Domain: {ctx.domain}")
        console.print(f"  Role: {ctx.role}")
        console.print(f"  Model: {ctx.model}")
        if skill_md.domain_context:
            console.print(f"  Domain context: loaded (DOMAIN.md)")
        else:
            console.print(f"  Domain context: [dim]none (no DOMAIN.md found)[/]")
        if skill_md.reflexion_context:
            console.print(f"  Reflexion entries: loaded (learned rules injected)")
        else:
            console.print(f"  Reflexion entries: [dim]none (no past corrections)[/]")
        console.print(f"  Prompt length: {len(ctx.system_prompt)} chars")
        console.print(f"  Input keys: {list(input_data.keys())}")
        console.print("\n[green]Validation passed.[/] Run without --dry-run to execute.")
        return

    # Execute via local runner
    from aspora_sdk.runner.local_runner import execute_skill

    console.print(f"[cyan]Executing {skill_name}...[/]")
    result = asyncio.run(execute_skill(ctx))

    if result.success:
        console.print(Panel(JSON(json.dumps(result.output, indent=2)), title="[green]Output"))
    else:
        console.print(Panel(JSON(json.dumps(result.output, indent=2)), title="[red]Error"))

    console.print(f"\n  Model: {result.model_used}")
    console.print(f"  Cost: ${result.cost_usd:.4f}")
    console.print(f"  Latency: {result.latency_ms:.0f}ms")

    if result.reasoning_trace:
        console.print("\n[dim]Reasoning trace:[/]")
        for step in result.reasoning_trace:
            console.print(f"  - {step}")

    if result.route_to:
        console.print(f"\n[yellow]Routes to: {result.route_to}[/]")
