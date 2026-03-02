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
@click.option(
    "--severity",
    type=click.Choice(["P0", "P1", "all"]),
    default=None,
    help="Filter by test severity: P0=failure-generated, P1=correction-generated.",
)
@click.option(
    "--evals",
    is_flag=True,
    default=False,
    help="Run workflow eval configs from evals/ directory.",
)
def test(skill_path: str, framework: str, skills_dir: str | None, severity: str | None, evals: bool):
    """Run tests for a skill.

    SKILL_PATH should be domain/skill-name, e.g. hr/interview-questions.
    """
    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()

    console = Console()

    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name[/]")
        raise SystemExit(1)

    domain, skill_name = parts
    root = Path(skills_dir) / domain / skill_name

    # Workflow evals mode (DEC-070)
    if evals:
        _run_evals(root, console)
        return

    tests_dir = root / "tests"

    if not tests_dir.exists():
        console.print(f"[red]Error: no tests directory at {tests_dir}[/]")
        raise SystemExit(1)

    exit_code = 0
    generated_dir = tests_dir / "generated"

    # Severity filter mode: run only specific generated test files
    if severity:
        if not generated_dir.exists():
            console.print("[yellow]No generated tests directory found.[/]")
            raise SystemExit(0)

        if severity in ("P0", "all"):
            # P0 = failure-generated tests
            for tf in sorted(generated_dir.glob("test_failure_*.py")):
                console.print(f"\n[cyan bold]Running P0 test: {tf.name}[/]")
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(tf), "-v"],
                    cwd=str(root),
                )
                if result.returncode != 0:
                    exit_code = 1

        if severity in ("P1", "all"):
            # P1 = correction-generated tests
            for tf in sorted(generated_dir.glob("test_correction_*.py")):
                console.print(f"\n[cyan bold]Running P1 test: {tf.name}[/]")
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(tf), "-v"],
                    cwd=str(root),
                )
                if result.returncode != 0:
                    exit_code = 1
    else:
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


def _run_evals(root: Path, console: Console) -> None:
    """Run workflow eval configs from evals/ directory (DEC-070)."""
    evals_dir = root / "evals"
    if not evals_dir.exists():
        console.print(f"[red]Error: no evals directory at {evals_dir}[/]")
        raise SystemExit(1)

    try:
        from agentura_sdk.testing.eval_runner import load_eval_configs, run_eval
    except ImportError as e:
        console.print(f"[red]Error: eval runner not available: {e}[/]")
        raise SystemExit(1)

    configs = load_eval_configs(root)
    if not configs:
        console.print("[yellow]No eval configs found.[/]")
        return

    exit_code = 0
    for config in configs:
        console.print(f"\n[cyan bold]Running eval: {config.name}[/]")
        try:
            import asyncio
            result = asyncio.run(run_eval(config, root))
            if result.passed:
                console.print(f"  [green]PASS[/] ({result.attempts} attempt(s))")
            else:
                console.print(f"  [red]FAIL[/]: {', '.join(result.failures)}")
                exit_code = 1
        except Exception as e:
            console.print(f"  [red]ERROR[/]: {e}")
            exit_code = 1

    if exit_code == 0:
        console.print("\n[green bold]All evals passed.[/]")
    else:
        console.print("\n[red bold]Some evals failed.[/]")
        raise SystemExit(exit_code)
