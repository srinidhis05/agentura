"""aspora get <resource> — Query resources from gateway (like kubectl get)."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table


@click.group("get")
def get():
    """Get resources from the platform."""
    pass


@get.command("skills")
@click.option("-d", "--domain", help="Filter by domain (namespace).")
@click.option("-r", "--role", help="Filter by role (manager/specialist/field).")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json", "wide"]), default="table")
def get_skills(domain: str | None, role: str | None, fmt: str):
    """List skills from the gateway."""
    from aspora_sdk.cli.gateway import list_skills
    import json

    console = Console()
    skills = list_skills(domain=domain)

    if role:
        skills = [s for s in skills if s.get("role") == role]

    if fmt == "json":
        console.print_json(json.dumps(skills, indent=2))
        return

    if not skills:
        console.print("[yellow]No skills found.[/]")
        return

    table = Table(title=f"Skills ({len(skills)})")
    table.add_column("Domain", style="cyan")
    table.add_column("Name", style="green bold")
    table.add_column("Role", style="magenta")
    table.add_column("Model", style="dim")
    table.add_column("Trigger", style="dim")

    if fmt == "wide":
        table.add_column("Description")
        table.add_column("Cost", style="dim")
        table.add_column("Guardrails", justify="right")
        table.add_column("Corrections", justify="right")

    for s in skills:
        row = [
            s.get("domain", ""),
            s.get("name", ""),
            s.get("role", ""),
            (s.get("model") or "").split("/")[-1],
            s.get("trigger", ""),
        ]
        if fmt == "wide":
            row.extend([
                (s.get("description") or "")[:50],
                s.get("cost_budget", ""),
                str(s.get("guardrails_count", 0)),
                str(s.get("corrections_count", 0)),
            ])
        table.add_row(*row)

    console.print(table)


@get.command("domains")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json"]), default="table")
def get_domains(fmt: str):
    """List domains (namespaces) with health metrics."""
    from aspora_sdk.cli.gateway import list_skills, list_executions
    import json

    console = Console()
    skills = list_skills()

    # Group by domain
    domains: dict[str, dict] = {}
    for s in skills:
        d = s.get("domain", "unknown")
        if d not in domains:
            domains[d] = {
                "name": d,
                "description": s.get("domain_description", ""),
                "owner": s.get("domain_owner", ""),
                "skills": 0,
                "roles": set(),
            }
        domains[d]["skills"] += 1
        domains[d]["roles"].add(s.get("role", ""))

    # Try to get execution counts
    try:
        execs = list_executions()
        for e in execs:
            d = e.get("skill", "").split("/")[0]
            if d in domains:
                domains[d].setdefault("executions", 0)
                domains[d]["executions"] = domains[d].get("executions", 0) + 1
    except Exception:
        pass

    domain_list = list(domains.values())
    for d in domain_list:
        d["roles"] = ", ".join(sorted(d["roles"]))

    if fmt == "json":
        console.print_json(json.dumps(domain_list, indent=2))
        return

    table = Table(title=f"Domains ({len(domain_list)})")
    table.add_column("Name", style="cyan bold")
    table.add_column("Description")
    table.add_column("Owner", style="dim")
    table.add_column("Skills", justify="right")
    table.add_column("Roles", style="magenta")
    table.add_column("Executions", justify="right")

    for d in sorted(domain_list, key=lambda x: x["name"]):
        table.add_row(
            d["name"],
            d.get("description", ""),
            d.get("owner", ""),
            str(d["skills"]),
            d["roles"],
            str(d.get("executions", 0)),
        )

    console.print(table)


@get.command("executions")
@click.option("-s", "--skill", help="Filter by skill (domain/name).")
@click.option("-n", "--limit", type=int, default=20, help="Max results.")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json"]), default="table")
def get_executions(skill: str | None, limit: int, fmt: str):
    """List execution history."""
    from aspora_sdk.cli.gateway import list_executions
    import json

    console = Console()

    try:
        execs = list_executions(skill=skill)[:limit]
    except Exception as e:
        console.print(f"[yellow]Could not fetch executions: {e}[/]")
        return

    if fmt == "json":
        console.print_json(json.dumps(execs, indent=2))
        return

    if not execs:
        console.print("[yellow]No executions found.[/]")
        return

    table = Table(title=f"Executions ({len(execs)})")
    table.add_column("ID", style="dim")
    table.add_column("Skill", style="cyan")
    table.add_column("Outcome")
    table.add_column("Cost", justify="right", style="dim")
    table.add_column("Latency", justify="right", style="dim")
    table.add_column("Model", style="dim")
    table.add_column("Timestamp", style="dim")

    outcome_styles = {
        "accepted": "green",
        "corrected": "yellow",
        "pending_review": "blue",
    }

    for e in execs:
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

    console.print(table)


@get.command("events")
@click.option("-d", "--domain", help="Filter by domain.")
@click.option("-t", "--type", "event_type", help="Filter by event type.")
@click.option("-n", "--limit", type=int, default=25, help="Max results.")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json"]), default="table")
def get_events(domain: str | None, event_type: str | None, limit: int, fmt: str):
    """List platform events (kubectl get events equivalent)."""
    from aspora_sdk.cli.gateway import list_events
    import json

    console = Console()
    events = list_events(domain=domain, event_type=event_type, limit=limit)

    if fmt == "json":
        console.print_json(json.dumps(events, indent=2))
        return

    if not events:
        console.print("[yellow]No events found.[/]")
        return

    table = Table(title=f"Events ({len(events)})")
    table.add_column("ID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Domain", style="magenta")
    table.add_column("Skill", style="green")
    table.add_column("Severity")
    table.add_column("Timestamp", style="dim")
    table.add_column("Message")

    severity_styles = {"info": "blue", "warning": "yellow", "error": "red"}

    for e in events:
        sev = e.get("severity", "info")
        style = severity_styles.get(sev, "")
        ts = e.get("timestamp", "")[:19] if e.get("timestamp") else ""
        table.add_row(
            e.get("event_id", ""),
            e.get("event_type", ""),
            e.get("domain", ""),
            e.get("skill", ""),
            f"[{style}]{sev}[/{style}]" if style else sev,
            ts,
            (e.get("message") or "")[:60],
        )

    console.print(table)


@get.command("threads")
@click.option("-n", "--limit", type=int, default=20, help="Max results.")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json"]), default="table")
def get_threads(limit: int, fmt: str):
    """Group executions by session/thread id."""
    from aspora_sdk.cli.gateway import list_executions
    import json

    console = Console()
    execs = list_executions()

    threads: dict[str, dict] = {}
    for e in execs:
        input_summary = e.get("input_summary") or {}
        if not isinstance(input_summary, dict):
            continue
        thread_id = input_summary.get("session_id") or input_summary.get("thread_id")
        if not thread_id:
            continue
        entry = threads.setdefault(
            thread_id,
            {"thread_id": thread_id, "runs": 0, "last_skill": "", "last_seen": ""},
        )
        entry["runs"] += 1
        ts = e.get("timestamp", "")
        if ts and ts > entry["last_seen"]:
            entry["last_seen"] = ts
            entry["last_skill"] = e.get("skill", "")

    thread_list = sorted(threads.values(), key=lambda t: t.get("last_seen", ""), reverse=True)[:limit]

    if fmt == "json":
        console.print_json(json.dumps(thread_list, indent=2))
        return

    if not thread_list:
        console.print("[yellow]No thread/session IDs found in inputs.[/]")
        return

    table = Table(title=f"Threads ({len(thread_list)})")
    table.add_column("Thread ID", style="cyan")
    table.add_column("Runs", justify="right")
    table.add_column("Last Skill", style="green")
    table.add_column("Last Seen", style="dim")

    for t in thread_list:
        table.add_row(
            t.get("thread_id", ""),
            str(t.get("runs", 0)),
            t.get("last_skill", ""),
            t.get("last_seen", "")[:19],
        )

    console.print(table)


@get.command("reflexions")
@click.option("-s", "--skill", help="Filter by skill.")
@click.option("-o", "--output", "fmt", type=click.Choice(["table", "json"]), default="table")
def get_reflexions(skill: str | None, fmt: str):
    """List learned rules (reflexion entries)."""
    from aspora_sdk.cli.gateway import get_analytics
    import json

    console = Console()

    # Reflexions are currently embedded in execution details
    # For now, read from local knowledge layer
    from pathlib import Path
    import os

    knowledge_dir = Path(os.environ.get("ASPORA_KNOWLEDGE_DIR", Path.cwd() / ".aspora"))
    reflexion_file = knowledge_dir / "reflexion_entries.json"

    if not reflexion_file.exists():
        console.print("[yellow]No reflexion entries found.[/]")
        return

    data = json.loads(reflexion_file.read_text())
    entries = data.get("entries", [])

    if skill:
        entries = [e for e in entries if e.get("skill", "") == skill]

    if fmt == "json":
        console.print_json(json.dumps(entries, indent=2))
        return

    if not entries:
        console.print("[yellow]No reflexion entries found.[/]")
        return

    table = Table(title=f"Reflexions ({len(entries)})")
    table.add_column("ID", style="violet")
    table.add_column("Skill", style="cyan")
    table.add_column("Rule")
    table.add_column("Confidence", justify="right")
    table.add_column("Validated", justify="right")

    for e in entries:
        validated = "[green]Yes[/]" if e.get("validated_by_test") else "[dim]No[/]"
        table.add_row(
            e.get("reflexion_id", ""),
            e.get("skill", ""),
            (e.get("rule") or "")[:60],
            f"{e.get('confidence', 0):.1f}",
            validated,
        )

    console.print(table)
