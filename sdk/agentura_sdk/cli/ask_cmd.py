"""agentura ask <query> — Route natural language to the right skill and execute."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel


def _compose_prompt(skill_md) -> str:
    """Build system prompt from WORKSPACE + DOMAIN + reflexion + SKILL body."""
    parts = []
    if skill_md.workspace_context:
        parts.append(skill_md.workspace_context)
    if skill_md.domain_context:
        parts.append(skill_md.domain_context)
    if skill_md.reflexion_context:
        parts.append(skill_md.reflexion_context)
    parts.append(skill_md.system_prompt)
    return "\n\n---\n\n".join(parts)


def _display_result(console: Console, result, skill_name: str) -> None:
    """Display skill execution result with Rich formatting."""
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


@click.command("ask")
@click.argument("query", nargs=-1, required=True)
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default=None,
    help="Root directory for skills.",
)
@click.option("--model", "model_override", help="Override model for target skill.")
@click.option("--dry-run", is_flag=True, help="Show routing result without executing.")
@click.option("--verbose", is_flag=True, help="Show routing details before execution.")
def ask(query: tuple[str, ...], skills_dir: str | None, model_override: str | None, dry_run: bool, verbose: bool):
    """Route a natural language query to the right skill and execute it.

    \b
    Examples:
      agentura ask "order UK131K is stuck"
      agentura ask my tickets
      agentura ask "simulate rule SameAmountMultiTxn" --dry-run
    """
    console = Console()
    query_str = " ".join(query)

    if not query_str.strip():
        console.print("[red]Error: query cannot be empty.[/]")
        raise SystemExit(1)

    # 1. Find skills directory
    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()
        if not Path(skills_dir).exists():
            console.print("[red]Error: skills directory not found. Set --skills-dir or AGENTURA_SKILLS_DIR.[/]")
            raise SystemExit(1)

    skills_path = Path(skills_dir)

    # 2. Build skill registry
    from agentura_sdk.runner.skill_registry import build_registry

    registry = build_registry(skills_path)
    if not registry.skills:
        console.print("[red]Error: no routable skills found.[/]")
        raise SystemExit(1)

    # 3. Route query via LLM
    from agentura_sdk.runner.router import route_query

    console.print(f"[dim]Routing: \"{query_str}\"...[/]")
    routing = asyncio.run(route_query(query_str, registry))

    if verbose or dry_run:
        console.print(Panel(
            f"  Domain: [cyan]{routing.domain}[/]\n"
            f"  Skill:  [green]{routing.skill_name}[/]\n"
            f"  Confidence: {routing.confidence:.0%}\n"
            f"  Entities: {routing.entities}\n"
            f"  Reasoning: {routing.reasoning}",
            title="[blue]Routing Result[/]",
        ))

    if dry_run:
        if routing.confidence >= 0.5:
            console.print(f"\n[green]Would execute:[/] agentura run {routing.domain}/{routing.skill_name}")
        else:
            console.print("\n[yellow]Low confidence — would show fallback.[/]")
        return

    # 4. Check confidence threshold
    if routing.confidence < 0.5:
        console.print(Panel(
            f"  Confidence: {routing.confidence:.0%}\n"
            f"  Reasoning: {routing.reasoning}\n\n"
            "  Try a more specific query, or run a skill directly:\n"
            "  [dim]agentura run <domain>/<skill-name>[/]",
            title="[yellow]Routing Uncertain[/]",
        ))
        raise SystemExit(1)

    # 5. Load and execute the target skill
    skill_path_str = f"{routing.domain}/{routing.skill_name}"
    root = skills_path / routing.domain / routing.skill_name

    if not root.exists():
        console.print(f"[red]Error: routed skill not found at {root}[/]")
        console.print(f"[dim]Try: agentura run <domain>/<skill-name>[/]")
        raise SystemExit(1)

    from agentura_sdk.runner.config_loader import load_config
    from agentura_sdk.runner.skill_loader import load_skill_md
    from agentura_sdk.types import SkillContext

    config = load_config(root / "agentura.config.yaml")
    skill_md = load_skill_md(root / "SKILL.md")

    input_data = {**routing.entities, "query": query_str}
    model = model_override or skill_md.metadata.model
    composed_prompt = _compose_prompt(skill_md)

    ctx = SkillContext(
        skill_name=skill_md.metadata.name,
        domain=skill_md.metadata.domain,
        role=skill_md.metadata.role,
        model=model,
        system_prompt=composed_prompt,
        input_data=input_data,
    )

    # 6. Execute and display
    from agentura_sdk.runner.local_runner import execute_skill

    console.print(f"[cyan]Executing {skill_path_str}...[/]")
    result = asyncio.run(execute_skill(ctx))
    _display_result(console, result, skill_md.metadata.name)
