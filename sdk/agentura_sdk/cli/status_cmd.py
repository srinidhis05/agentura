"""agentura status — Platform health check (like kubectl cluster-info)."""

import click
from rich.console import Console
from rich.panel import Panel


@click.command("status")
def status():
    """Show platform health status."""
    from agentura_sdk.cli.gateway import health_check, get_gateway_url, list_skills, get_analytics

    console = Console()

    # Gateway health
    h = health_check()
    gw_status = "[green]Online[/]" if h.get("gateway") else f"[red]Offline[/] ({h.get('error', 'unknown')})"

    console.print(Panel(
        f"Gateway:  {gw_status}\n"
        f"URL:      {get_gateway_url()}",
        title="[bold]Agentura Platform Status[/]",
    ))

    if not h.get("gateway"):
        console.print("\n[dim]Start the platform: docker compose up -d[/]")
        return

    # Skills + domains
    try:
        skills = list_skills()
        domains = sorted(set(s.get("domain", "") for s in skills))
        models = sorted(set(s.get("model", "") for s in skills))

        console.print(f"\n  Domains:    {len(domains)} ({', '.join(domains)})")
        console.print(f"  Skills:     {len(skills)}")
        console.print(f"  Models:     {len(models)}")
        for m in models:
            console.print(f"              [dim]{m}[/]")
    except Exception as e:
        console.print(f"\n  [yellow]Could not fetch skills: {e}[/]")

    # Analytics summary
    try:
        a = get_analytics()
        console.print(f"\n  Executions: {a.get('total_executions', 0)}")
        console.print(f"  Accept rate: {round(a.get('accept_rate', 0) * 100)}%")
        console.print(f"  Total cost:  ${a.get('total_cost_usd', 0):.2f}")
        console.print(f"  Corrections: {a.get('total_corrections', 0)}")
        console.print(f"  Reflexions:  {a.get('total_reflexions', 0)}")
    except Exception:
        pass

    console.print()
