"""agentura describe <resource> <name> — Detailed view (like kubectl describe)."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown


@click.group("describe")
def describe():
    """Show detailed information about a resource."""
    pass


@describe.command("skill")
@click.argument("skill_path")
def describe_skill(skill_path: str):
    """Describe a skill in detail.

    SKILL_PATH should be domain/skill-name, e.g. hr/interview-questions.
    """
    from agentura_sdk.cli.gateway import get_skill_detail

    console = Console()
    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name[/]")
        raise SystemExit(1)

    domain, skill = parts

    try:
        d = get_skill_detail(domain, skill)
    except Exception as e:
        console.print(f"[red]Error fetching skill detail: {e}[/]")
        raise SystemExit(1)

    # Header
    console.print(Panel(
        f"[bold]{d.get('name', skill)}[/]\n"
        f"Domain:      {d.get('domain', domain)}\n"
        f"Role:        {d.get('role', '')}\n"
        f"Model:       {d.get('model', '')}\n"
        f"Trigger:     {d.get('trigger', '')}\n"
        f"Cost budget: {d.get('cost_budget', '')}\n"
        f"Timeout:     {d.get('timeout', '')}",
        title=f"[cyan]{domain}/{skill}[/]",
    ))

    # Description
    desc = d.get("description", "")
    if desc:
        console.print(f"\n[bold]Description:[/] {desc}\n")

    # Task description
    task = d.get("task_description", "")
    if task:
        console.print(Panel(Markdown(task), title="Task Description"))

    # Input schema
    input_schema = d.get("input_schema", "")
    if input_schema:
        console.print(Panel(Markdown(input_schema), title="Input Schema"))

    # Output schema
    output_schema = d.get("output_schema", "")
    if output_schema:
        console.print(Panel(Markdown(output_schema), title="Output Schema"))

    # Guardrails
    guardrails = d.get("skill_guardrails", [])
    if guardrails:
        console.print("\n[bold]Guardrails:[/]")
        for g in guardrails:
            console.print(f"  - {g}")

    # MCP tools
    mcp = d.get("mcp_tools", [])
    if mcp:
        console.print(f"\n[bold]MCP Tools:[/] {', '.join(mcp)}")

    # Triggers
    triggers = d.get("triggers", [])
    if triggers:
        console.print("\n[bold]Triggers:[/]")
        for t in triggers:
            pattern = t.get("pattern", t.get("description", str(t)))
            trigger_type = t.get("type", "")
            console.print(f"  [{trigger_type}] {pattern}")

    # Feedback config
    feedback = d.get("feedback_enabled")
    if feedback is not None:
        status = "[green]Enabled[/]" if feedback else "[red]Disabled[/]"
        console.print(f"\n[bold]Feedback loop:[/] {status}")

    console.print()


@describe.command("execution")
@click.argument("execution_id")
def describe_execution(execution_id: str):
    """Describe an execution with full trace and correction chain."""
    from agentura_sdk.cli.gateway import get_execution

    console = Console()

    try:
        data = get_execution(execution_id)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise SystemExit(1)

    exec_data = data.get("execution", data)
    corrections = data.get("corrections", [])
    reflexions = data.get("reflexions", [])

    # Header
    outcome = exec_data.get("outcome", "")
    outcome_colors = {"accepted": "green", "corrected": "yellow", "pending_review": "blue"}
    color = outcome_colors.get(outcome, "white")

    console.print(Panel(
        f"[bold]{exec_data.get('execution_id', execution_id)}[/]\n"
        f"Skill:    {exec_data.get('skill', '')}\n"
        f"Outcome:  [{color}]{outcome}[/{color}]\n"
        f"Model:    {exec_data.get('model_used', '')}\n"
        f"Cost:     ${exec_data.get('cost_usd', 0):.4f}\n"
        f"Latency:  {exec_data.get('latency_ms', 0) / 1000:.1f}s\n"
        f"Time:     {exec_data.get('timestamp', '')}",
        title="Execution",
    ))

    # Input
    import json
    inp = exec_data.get("input_summary", {})
    console.print(Panel(
        json.dumps(inp, indent=2) if isinstance(inp, dict) else str(inp),
        title="Input",
    ))

    # Output
    out = exec_data.get("output_summary", {})
    console.print(Panel(
        json.dumps(out, indent=2) if isinstance(out, dict) else str(out),
        title="Output",
    ))

    # Reflexion applied
    refl = exec_data.get("reflexion_applied")
    if refl:
        console.print(Panel(f"[violet]{refl}[/]", title="Reflexion Applied"))

    # Correction chain
    if corrections or reflexions:
        console.print("\n[bold]Correction Chain:[/]")

        chain_parts = [f"[blue]EXEC[/]"]
        for c in corrections:
            chain_parts.append(f"[yellow]{c.get('correction_id', '')}[/]")
        for r in reflexions:
            chain_parts.append(f"[violet]{r.get('reflexion_id', '')}[/]")
        console.print("  " + " → ".join(chain_parts))

        for c in corrections:
            console.print(Panel(
                f"{c.get('user_correction', '')}\n\n"
                f"[dim]{c.get('timestamp', '')}[/]",
                title=f"[yellow]Correction {c.get('correction_id', '')}[/]",
            ))

        for r in reflexions:
            validated = "[green]Yes[/]" if r.get("validated_by_test") else "[dim]No[/]"
            console.print(Panel(
                f"Rule: {r.get('rule', '')}\n"
                f"Applies when: {r.get('applies_when', '')}\n"
                f"Confidence: {r.get('confidence', 0)}\n"
                f"Validated by test: {validated}",
                title=f"[violet]Reflexion {r.get('reflexion_id', '')}[/]",
            ))

    console.print()
