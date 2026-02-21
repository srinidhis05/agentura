"""Aspora CLI — Create, run, test, and manage skills (like kubectl for AI agents)."""

import click

from aspora_sdk.cli.apply_cmd import apply
from aspora_sdk.cli.approve_cmd import approve
from aspora_sdk.cli.correct import correct
from aspora_sdk.cli.create import create
from aspora_sdk.cli.describe_cmd import describe
from aspora_sdk.cli.get_cmd import get
from aspora_sdk.cli.logs_cmd import logs
from aspora_sdk.cli.memory_cmd import memory
from aspora_sdk.cli.replay import replay
from aspora_sdk.cli.run import run
from aspora_sdk.cli.status_cmd import status
from aspora_sdk.cli.test_cmd import test
from aspora_sdk.cli.validate import validate
from aspora_sdk.cli.watch_cmd import watch


@click.group()
@click.version_option(package_name="aspora-sdk")
def cli():
    """Aspora — Kubernetes for AI Agents.

    Create, deploy, and manage AI skills across your organization.

    \b
    Local operations:
      aspora create skill <domain>/<name>    Scaffold a new skill
      aspora validate <domain>/<name>        Validate skill structure
      aspora run <domain>/<name>             Execute a skill locally
      aspora correct <domain>/<name>         Submit correction → auto-gen tests
      aspora test <domain>/<name>            Run DeepEval + Promptfoo tests
      aspora apply -f <path>                 Deploy skills to gateway

    \b
    Gateway operations:
      aspora status                          Platform health check
      aspora get skills                      List skills from gateway
      aspora get domains                     List domains with health
      aspora get executions                  List execution history
      aspora get events                      List platform events
      aspora get threads                     Group executions by session/thread
      aspora get reflexions                  List learned rules
      aspora describe skill <d/n>            Detailed skill view
      aspora describe execution <id>         Execution trace + corrections
      aspora logs <execution-id>             View reasoning trace
      aspora memory status                   Memory store status
      aspora memory search "query"           Search shared memory
      aspora memory prompt <d/n>             Assembled prompt (DOMAIN + reflexion + SKILL)
      aspora replay <execution-id>           Re-run a past execution
      aspora approve <execution-id>          Approve/reject pending execution
      aspora watch                           Live execution feed
      aspora get approvals                   List pending approvals
    """
    pass


@cli.command("list")
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default="skills",
    help="Root directory containing skills.",
)
def list_skills(skills_dir: str):
    """List all skills in the local workspace."""
    from pathlib import Path

    from rich.console import Console
    from rich.table import Table

    console = Console()
    root = Path(skills_dir)

    if not root.exists():
        console.print(f"[yellow]Skills directory not found: {root}[/]")
        return

    table = Table(title="Local Skills")
    table.add_column("Domain", style="cyan")
    table.add_column("Skill", style="green")
    table.add_column("Role", style="magenta")
    table.add_column("Path", style="dim")

    found = False
    for config_file in sorted(root.rglob("aspora.config.yaml")):
        from aspora_sdk.runner.config_loader import load_config

        try:
            config = load_config(config_file)
            for skill in config.skills:
                table.add_row(
                    config.domain.name,
                    skill.name,
                    skill.role,
                    str(config_file.parent.relative_to(root)),
                )
                found = True
        except Exception as e:
            console.print(f"[red]Error loading {config_file}: {e}[/]")

    if found:
        console.print(table)
    else:
        console.print("[yellow]No skills found. Create one with: aspora create skill <domain>/<name>[/]")


# Local operations
cli.add_command(apply)
cli.add_command(correct)
cli.add_command(create)
cli.add_command(run)
cli.add_command(test)
cli.add_command(validate)
cli.add_command(replay)

# Gateway operations
cli.add_command(approve)
cli.add_command(describe)
cli.add_command(get)
cli.add_command(logs)
cli.add_command(status)
cli.add_command(memory)
cli.add_command(watch)


if __name__ == "__main__":
    cli()
