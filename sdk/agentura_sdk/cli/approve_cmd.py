"""agentura approve <execution-id> — Approve or reject a pending execution."""

from __future__ import annotations

import click
from rich.console import Console


@click.command("approve")
@click.argument("execution_id")
@click.option("--reject", is_flag=True, help="Reject instead of approve.")
@click.option("--notes", default="", help="Reviewer notes.")
def approve(execution_id: str, reject: bool, notes: str):
    """Approve or reject a pending execution.

    \b
    Examples:
      agentura approve exec-abc123                     # approve
      agentura approve exec-abc123 --reject            # reject
      agentura approve exec-abc123 --notes "LGTM"      # approve with notes
      agentura approve exec-abc123 --reject --notes "Wrong format"
    """
    from agentura_sdk.cli.gateway import approve_execution

    console = Console()
    action = "Rejecting" if reject else "Approving"
    console.print(f"[cyan]{action}[/] execution [bold]{execution_id}[/]...")

    try:
        result = approve_execution(execution_id, approved=not reject, notes=notes)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise SystemExit(1)

    status = result.get("status", "unknown")
    style = "green" if status in ("approved", "accepted") else "red" if status == "rejected" else "yellow"
    console.print(f"[{style}]Result: {status}[/{style}]")

    if result.get("reviewer_notes"):
        console.print(f"  Notes: {result['reviewer_notes']}")
