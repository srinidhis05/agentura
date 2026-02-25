"""agentura watch — Live execution feed (like kubectl get pods --watch)."""

from __future__ import annotations

import time

import click
from rich.console import Console
from rich.live import Live
from rich.table import Table


def _build_table(executions: list[dict], title: str) -> Table:
    """Build a Rich table from executions."""
    outcome_styles = {
        "accepted": "green",
        "corrected": "yellow",
        "pending_review": "blue",
        "pending_approval": "bright_yellow",
        "approved": "green",
        "rejected": "red",
    }

    table = Table(title=title)
    table.add_column("ID", style="dim")
    table.add_column("Skill", style="cyan")
    table.add_column("Outcome")
    table.add_column("Cost", justify="right", style="dim")
    table.add_column("Latency", justify="right", style="dim")
    table.add_column("Model", style="dim")
    table.add_column("Timestamp", style="dim")

    for e in executions:
        outcome = e.get("outcome", "")
        style = outcome_styles.get(outcome, "")
        ts = e.get("timestamp", "")[:19] if e.get("timestamp") else ""
        table.add_row(
            e.get("execution_id", ""),
            e.get("skill", ""),
            f"[{style}]{outcome}[/{style}]" if style else outcome,
            f"${e.get('cost_usd', 0):.4f}",
            f"{e.get('latency_ms', 0) / 1000:.1f}s",
            (e.get("model_used") or "").split("/")[-1],
            ts,
        )

    return table


@click.command("watch")
@click.option("-s", "--skill", help="Filter by skill (domain/name).")
@click.option("-n", "--limit", type=int, default=20, help="Max rows to display.")
@click.option("--interval", type=float, default=2.0, help="Poll interval in seconds.")
def watch(skill: str | None, limit: int, interval: float):
    """Watch executions in real-time (Ctrl+C to stop).

    \b
    Examples:
      agentura watch                      # all executions
      agentura watch --skill hr/triage     # filtered
      agentura watch --interval 5         # slower polling
    """
    from agentura_sdk.cli.gateway import list_executions

    console = Console()
    console.print("[dim]Watching executions (Ctrl+C to stop)...[/]\n")

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                try:
                    execs = list_executions(skill=skill)[:limit]
                    title = f"Executions — {skill}" if skill else "Executions (live)"
                    live.update(_build_table(execs, title))
                except Exception as e:
                    live.update(f"[red]Error fetching: {e}[/]")
                time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim]Watch stopped.[/]")
