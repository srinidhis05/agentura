"""agentura memory <status|search|prompt> — Memory explorer commands."""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table


@click.group("memory")
def memory():
    """Inspect shared memory (executions, corrections, reflexions)."""
    pass


@memory.command("status")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json"]), default="table")
def memory_status(fmt: str):
    """Show memory store status and counts."""
    from agentura_sdk.cli.gateway import get_memory_status

    console = Console()
    data = get_memory_status()

    if fmt == "json":
        console.print_json(json.dumps(data, indent=2))
        return

    table = Table(title="Memory Status")
    table.add_column("Store", style="cyan")
    table.add_column("Executions", justify="right")
    table.add_column("Corrections", justify="right")
    table.add_column("Reflexions", justify="right")
    table.add_column("Tests", justify="right")

    table.add_row(
        data.get("store_type", "unknown"),
        str(data.get("execution_memories", 0)),
        str(data.get("correction_memories", 0)),
        str(data.get("reflexion_memories", 0)),
        str(data.get("test_memories", 0)),
    )
    console.print(table)


@memory.command("search")
@click.argument("query")
@click.option("-n", "--limit", type=int, default=10, help="Max results.")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json"]), default="table")
def memory_search(query: str, limit: int, fmt: str):
    """Search across shared memory with a text query."""
    from agentura_sdk.cli.gateway import memory_search as _search

    console = Console()
    data = _search(query=query, limit=limit)
    results = data.get("results", [])

    if fmt == "json":
        console.print_json(json.dumps(results, indent=2))
        return

    if not results:
        console.print("[yellow]No memory matches found.[/]")
        return

    table = Table(title=f"Memory Matches ({len(results)})")
    table.add_column("Type", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Skill", style="green")
    table.add_column("Score", justify="right")
    table.add_column("Snippet")

    for r in results:
        table.add_row(
            r.get("type", ""),
            r.get("id", ""),
            r.get("skill", ""),
            f"{r.get('score', 0):.2f}",
            (r.get("snippet") or "")[:80],
        )

    console.print(table)


@memory.command("prompt")
@click.argument("skill_path")
@click.option("-o", "--output", "fmt", type=click.Choice(["json", "text"]), default="text")
def memory_prompt(skill_path: str, fmt: str):
    """Show the assembled prompt (DOMAIN + reflexion + SKILL)."""
    from agentura_sdk.cli.gateway import get_prompt_assembly

    console = Console()
    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name[/]")
        raise SystemExit(1)

    domain, skill = parts
    data = get_prompt_assembly(domain, skill)

    if fmt == "json":
        console.print_json(json.dumps(data, indent=2))
        return

    prompt = data.get("prompt", "")
    console.print(prompt if prompt else "[yellow]No prompt assembly available.[/]")


@memory.command("reflexions")
@click.option("--skill", default=None, help="Filter by skill path (domain/name).")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json"]), default="table")
def memory_reflexions(skill: str | None, fmt: str):
    """Show reflexion rules with MemRL utility scores."""
    from agentura_sdk.memory import get_memory_store

    console = Console()
    store = get_memory_store()
    entries = store.get_all_reflexions()

    if skill:
        entries = [e for e in entries if e.get("skill") == skill]

    if fmt == "json":
        console.print_json(json.dumps(entries, indent=2, default=str))
        return

    if not entries:
        console.print("[yellow]No reflexion entries found.[/]")
        return

    table = Table(title="Reflexion Rules (MemRL)")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Skill", style="cyan")
    table.add_column("Rule", max_width=50)
    table.add_column("Utility", justify="right")
    table.add_column("Inj", justify="right", style="dim")
    table.add_column("Helped", justify="right", style="dim")
    table.add_column("Conf", justify="right")
    table.add_column("Valid", justify="center")
    table.add_column("Source", style="dim")

    for e in entries:
        utility = e.get("utility_score", 0.5)
        pct = f"{utility:.0%}"
        if utility >= 0.6:
            color = "green"
        elif utility >= 0.3:
            color = "yellow"
        else:
            color = "red"

        table.add_row(
            e.get("reflexion_id", ""),
            e.get("skill", ""),
            (e.get("rule", "") or "")[:50],
            f"[{color}]{pct}[/{color}]",
            str(e.get("times_injected", 0)),
            str(e.get("times_helped", 0)),
            f"{e.get('confidence', 0):.0%}",
            "[green]Y[/]" if e.get("validated_by_test") else "[dim]N[/]",
            e.get("source", "correction"),
        )

    console.print(table)
