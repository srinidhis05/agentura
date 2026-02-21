"""aspora replay <execution_id> — Re-run a past execution via gateway."""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel


@click.command("replay")
@click.argument("execution_id")
@click.option("--model", "model_override", help="Override model for replay.")
@click.option("--dry-run", is_flag=True, help="Validate without calling model.")
@click.option("-o", "--output", "fmt", type=click.Choice(["pretty", "json"]), default="pretty")
def replay(execution_id: str, model_override: str | None, dry_run: bool, fmt: str):
    """Replay an execution using the original input."""
    from aspora_sdk.cli.gateway import get_execution, execute_skill

    console = Console()
    data = get_execution(execution_id)
    exec_data = data.get("execution") or {}

    skill_path = exec_data.get("skill", "")
    if "/" not in skill_path:
        console.print("[red]Error: execution missing skill path.[/]")
        raise SystemExit(1)

    domain, skill = skill_path.split("/", 1)
    input_data = exec_data.get("input_summary") or {}

    console.print(f"[cyan]Replaying {skill_path}[/] ({execution_id})")
    result = execute_skill(domain, skill, input_data, model_override=model_override, dry_run=dry_run)

    if fmt == "json":
        console.print_json(json.dumps(result, indent=2))
        return

    title = "[green]Output" if result.get("success", False) else "[red]Error"
    console.print(Panel(JSON(json.dumps(result.get("output", {}), indent=2)), title=title))

    if result.get("model_used"):
        console.print(f"\n  Model: {result.get('model_used')}")
    if result.get("cost_usd") is not None:
        console.print(f"  Cost: ${result.get('cost_usd', 0):.4f}")
    if result.get("latency_ms") is not None:
        console.print(f"  Latency: {result.get('latency_ms', 0):.0f}ms")
