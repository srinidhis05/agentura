"""agentura test <domain>/<name> — Run tests for a skill."""

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console


@click.command("test")
@click.argument("skill_path")
@click.option(
    "--framework",
    type=click.Choice(["deepeval", "promptfoo", "all"]),
    default="all",
    help="Test framework to run.",
)
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default=None,
    help="Root directory for skills.",
)
def test(skill_path: str, framework: str, skills_dir: str | None):
    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()
    """Run tests for a skill.

    SKILL_PATH should be domain/skill-name, e.g. hr/interview-questions.
    """
    console = Console()

    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name[/]")
        raise SystemExit(1)

    domain, skill_name = parts
    root = Path(skills_dir) / domain / skill_name
    tests_dir = root / "tests"

    if not tests_dir.exists():
        console.print(f"[red]Error: no tests directory at {tests_dir}[/]")
        raise SystemExit(1)

    exit_code = 0

    if framework in ("deepeval", "all"):
        deepeval_file = tests_dir / "test_deepeval.py"
        if deepeval_file.exists():
            console.print("\n[cyan bold]Running DeepEval tests...[/]")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(deepeval_file), "-v"],
                cwd=str(root),
            )
            if result.returncode != 0:
                exit_code = 1
        else:
            console.print("[yellow]No DeepEval test file found, skipping.[/]")

    if framework in ("promptfoo", "all"):
        promptfoo_file = tests_dir / "test_promptfoo.yaml"
        if promptfoo_file.exists():
            console.print("\n[cyan bold]Running Promptfoo tests...[/]")
            result = subprocess.run(
                ["promptfoo", "eval", "-c", str(promptfoo_file)],
                cwd=str(root),
            )
            if result.returncode != 0:
                exit_code = 1
        else:
            console.print("[yellow]No Promptfoo test file found, skipping.[/]")

    if exit_code == 0:
        console.print("\n[green bold]All tests passed.[/]")
    else:
        console.print("\n[red bold]Some tests failed.[/]")
        raise SystemExit(exit_code)
