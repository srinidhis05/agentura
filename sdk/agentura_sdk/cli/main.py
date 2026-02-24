"""Agentura CLI — Create, run, test, and manage skills (like kubectl for AI agents)."""

import click

from agentura_sdk.cli.apply_cmd import apply
from agentura_sdk.cli.approve_cmd import approve
from agentura_sdk.cli.correct import correct
from agentura_sdk.cli.cortex_cmd import cortex
from agentura_sdk.cli.create import create
from agentura_sdk.cli.describe_cmd import describe
from agentura_sdk.cli.get_cmd import get
from agentura_sdk.cli.logs_cmd import logs
from agentura_sdk.cli.memory_cmd import memory
from agentura_sdk.cli.replay import replay
from agentura_sdk.cli.run import run
from agentura_sdk.cli.status_cmd import status
from agentura_sdk.cli.test_cmd import test
from agentura_sdk.cli.validate import validate
from agentura_sdk.cli.watch_cmd import watch


@click.group()
@click.version_option(package_name="agentura-sdk")
def cli():
    """Agentura — Kubernetes for AI Agents.

    Create, deploy, and manage AI skills across your organization.

    \b
    Local operations:
      agentura create skill <domain>/<name>    Scaffold a new skill
      agentura validate <domain>/<name>        Validate skill structure
      agentura run <domain>/<name>             Execute a skill locally
      agentura correct <domain>/<name>         Submit correction → auto-gen tests
      agentura test <domain>/<name>            Run DeepEval + Promptfoo tests
      agentura apply -f <path>                 Deploy skills to gateway

    \b
    Gateway operations:
      agentura status                          Platform health check
      agentura get skills                      List skills from gateway
      agentura get domains                     List domains with health
      agentura get executions                  List execution history
      agentura get events                      List platform events
      agentura get threads                     Group executions by session/thread
      agentura get reflexions                  List learned rules
      agentura describe skill <d/n>            Detailed skill view
      agentura describe execution <id>         Execution trace + corrections
      agentura logs <execution-id>             View reasoning trace
      agentura memory status                   Memory store status
      agentura memory search "query"           Search shared memory
      agentura memory prompt <d/n>             Assembled prompt (DOMAIN + reflexion + SKILL)
      agentura replay <execution-id>           Re-run a past execution
      agentura approve <execution-id>          Approve/reject pending execution
      agentura watch                           Live execution feed
      agentura get approvals                   List pending approvals
    """
    pass


@cli.command("list")
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default=None,
    help="Root directory containing skills.",
)
def list_skills(skills_dir: str | None):
    """List all skills in the local workspace."""
    from pathlib import Path

    from rich.console import Console
    from rich.table import Table

    console = Console()

    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()

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
    for config_file in sorted(root.rglob("agentura.config.yaml")):
        from agentura_sdk.runner.config_loader import load_config

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
        console.print("[yellow]No skills found. Create one with: agentura create skill <domain>/<name>[/]")


# Local operations
cli.add_command(apply)
cli.add_command(correct)
cli.add_command(cortex)
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
