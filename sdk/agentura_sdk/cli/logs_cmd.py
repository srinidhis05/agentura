"""agentura logs <execution-id> — View reasoning trace (like kubectl logs)."""

import json

import click
from rich.console import Console
from rich.panel import Panel


@click.command("logs")
@click.argument("execution_id")
@click.option("--raw", is_flag=True, help="Raw JSON output.")
def logs(execution_id: str, raw: bool):
    """View the reasoning trace and output of an execution.

    EXECUTION_ID is the ID from 'agentura get executions'.
    """
    from agentura_sdk.cli.gateway import get_execution

    console = Console()

    try:
        data = get_execution(execution_id)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise SystemExit(1)

    exec_data = data.get("execution", data)

    if raw:
        console.print_json(json.dumps(data, indent=2))
        return

    # Header line (like kubectl logs prefix)
    skill = exec_data.get("skill", "unknown")
    ts = exec_data.get("timestamp", "")[:19]
    model = (exec_data.get("model_used") or "").split("/")[-1]
    console.print(f"[dim]{ts}[/] [cyan]{skill}[/] [dim]({model})[/]")
    console.print()

    # Input
    inp = exec_data.get("input_summary", {})
    if inp:
        console.print("[dim]--- input ---[/]")
        if isinstance(inp, dict):
            for k, v in inp.items():
                console.print(f"  {k}: {v}")
        else:
            console.print(f"  {inp}")
        console.print()

    # Reflexion applied (context that was injected)
    refl = exec_data.get("reflexion_applied")
    if refl:
        console.print(f"[dim]--- reflexion applied ---[/]")
        console.print(f"  [violet]{refl}[/]")
        console.print()

    # Output
    out = exec_data.get("output_summary", {})
    console.print("[dim]--- output ---[/]")
    if isinstance(out, dict):
        console.print(json.dumps(out, indent=2))
    else:
        console.print(str(out))
    console.print()

    # Metrics
    cost = exec_data.get("cost_usd", 0)
    latency = exec_data.get("latency_ms", 0)
    outcome = exec_data.get("outcome", "")
    console.print(f"[dim]--- metrics ---[/]")
    console.print(f"  outcome: {outcome}")
    console.print(f"  cost:    ${cost:.4f}")
    console.print(f"  latency: {latency / 1000:.1f}s")

    # Corrections
    corrections = data.get("corrections", [])
    if corrections:
        console.print()
        console.print("[dim]--- corrections ---[/]")
        for c in corrections:
            console.print(f"  [{c.get('correction_id', '')}] {c.get('user_correction', '')}")

    # Reflexions generated
    reflexions = data.get("reflexions", [])
    if reflexions:
        console.print()
        console.print("[dim]--- reflexions generated ---[/]")
        for r in reflexions:
            validated = "validated" if r.get("validated_by_test") else "unvalidated"
            console.print(f"  [{r.get('reflexion_id', '')}] {r.get('rule', '')} ({validated})")

    console.print()
