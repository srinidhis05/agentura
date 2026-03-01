"""Fleet CLI commands — manage parallel pipeline sessions."""

import asyncio
import sys

import click


def _gateway_url() -> str:
    import os
    return os.environ.get("AGENTURA_GATEWAY_URL", "http://localhost:3001")


def _get(path: str) -> dict | list:
    import httpx
    url = f"{_gateway_url()}{path}"
    resp = httpx.get(url, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


def _post(path: str) -> dict:
    import httpx
    url = f"{_gateway_url()}{path}"
    resp = httpx.post(url, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


@click.group()
def fleet():
    """Manage parallel fleet sessions.

    \b
    Fleet sessions track parallel agent executions triggered by PRs or manual runs.

      agentura fleet list                     List all fleet sessions
      agentura fleet get <session-id>         Session detail with agents
      agentura fleet watch <session-id>       Live SSE stream
      agentura fleet cancel <session-id>      Cancel a running session
    """
    pass


@fleet.command("list")
@click.option("--status", type=click.Choice(["running", "completed", "failed", "cancelled", "all"]),
              default="all", help="Filter by status.")
def fleet_list(status: str):
    """List fleet sessions."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    params = f"?status={status}" if status != "all" else ""

    try:
        sessions = _get(f"/api/v1/fleet/sessions{params}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        return

    if not sessions:
        console.print("[yellow]No fleet sessions found.[/]")
        return

    table = Table(title="Fleet Sessions")
    table.add_column("Session ID", style="cyan")
    table.add_column("Repo", style="dim")
    table.add_column("PR", style="blue")
    table.add_column("Status", style="bold")
    table.add_column("Agents", justify="right")
    table.add_column("Cost", justify="right", style="green")
    table.add_column("Created")

    for s in sessions:
        status_style = {
            "running": "[blue]running[/]",
            "completed": "[green]completed[/]",
            "failed": "[red]failed[/]",
            "cancelled": "[yellow]cancelled[/]",
        }.get(s.get("status", ""), s.get("status", ""))

        completed = s.get("completed_agents", 0)
        total = s.get("total_agents", 0)
        table.add_row(
            s.get("session_id", ""),
            s.get("repo", "—"),
            f"#{s.get('pr_number', '')}" if s.get("pr_number") else "—",
            status_style,
            f"{completed}/{total}",
            f"${s.get('total_cost_usd', 0):.3f}",
            s.get("created_at", "")[:19],
        )

    console.print(table)


@fleet.command("get")
@click.argument("session_id")
def fleet_get(session_id: str):
    """Get fleet session detail with agents."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    try:
        session = _get(f"/api/v1/fleet/sessions/{session_id}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        return

    # Session info
    console.print(Panel(
        f"Pipeline: {session.get('pipeline_name', '')}\n"
        f"Repo: {session.get('repo', '—')}\n"
        f"PR: #{session.get('pr_number', '—')} ({session.get('pr_url', '')})\n"
        f"Status: {session.get('status', '')}\n"
        f"Cost: ${session.get('total_cost_usd', 0):.3f}\n"
        f"Created: {session.get('created_at', '')}",
        title=f"Fleet Session {session_id}",
    ))

    # Agents table
    agents = session.get("agents", [])
    if agents:
        table = Table(title="Agents")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Skill", style="dim")
        table.add_column("Status")
        table.add_column("Success")
        table.add_column("Cost", justify="right")
        table.add_column("Latency", justify="right")
        table.add_column("Error")

        for a in agents:
            success = "[green]yes[/]" if a.get("success") else "[red]no[/]" if a.get("status") in ("completed", "failed") else "—"
            table.add_row(
                a.get("agent_id", ""),
                a.get("skill_path", ""),
                a.get("status", ""),
                success,
                f"${a.get('cost_usd', 0):.3f}",
                f"{a.get('latency_ms', 0):.0f}ms",
                a.get("error_message", "") or "—",
            )

        console.print(table)


@fleet.command("watch")
@click.argument("session_id")
def fleet_watch(session_id: str):
    """Watch a fleet session via live SSE stream."""
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table

    console = Console()
    console.print(f"[blue]Watching fleet session {session_id}...[/]")
    console.print("[dim]Press Ctrl+C to stop.[/]\n")

    agents_state: dict[str, dict] = {}

    def build_table() -> Table:
        table = Table(title=f"Fleet {session_id}")
        table.add_column("Agent", style="cyan")
        table.add_column("Status")
        table.add_column("Cost", justify="right")
        table.add_column("Latency", justify="right")
        for aid, state in sorted(agents_state.items()):
            status_str = state.get("status", "pending")
            if status_str == "completed" and state.get("success"):
                status_str = "[green]passed[/]"
            elif status_str == "failed" or (status_str == "completed" and not state.get("success")):
                status_str = "[red]failed[/]"
            elif status_str == "running":
                status_str = "[blue]running[/]"
            table.add_row(
                aid,
                status_str,
                f"${state.get('cost_usd', 0):.3f}",
                f"{state.get('latency_ms', 0):.0f}ms",
            )
        return table

    async def _stream():
        import httpx
        url = f"{_gateway_url()}/api/v1/fleet/sessions/{session_id}/stream"
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url) as resp:
                buffer = ""
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    frames = buffer.split("\n\n")
                    buffer = frames.pop()
                    for frame in frames:
                        if not frame.strip():
                            continue
                        event_type = ""
                        data_str = ""
                        for line in frame.split("\n"):
                            if line.startswith("event: "):
                                event_type = line[7:].strip()
                            elif line.startswith("data: "):
                                data_str = line[6:]
                        if not event_type or not data_str:
                            continue
                        import json
                        try:
                            data = json.loads(data_str)
                        except Exception:
                            continue
                        if event_type == "agent_update":
                            agents_state[data["agent_id"]] = data
                        elif event_type == "session_done":
                            return data

    try:
        with Live(build_table(), console=console, refresh_per_second=2) as live:
            async def _run():
                result = await _stream()
                live.update(build_table())
                return result
            result = asyncio.run(_run())
            if result:
                console.print(f"\n[bold]Session {result.get('status', 'done')}[/]")
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/]")


@fleet.command("cancel")
@click.argument("session_id")
def fleet_cancel(session_id: str):
    """Cancel a running fleet session."""
    from rich.console import Console

    console = Console()

    try:
        result = _post(f"/api/v1/fleet/sessions/{session_id}/cancel")
        console.print(f"[green]Session {session_id} cancelled.[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
