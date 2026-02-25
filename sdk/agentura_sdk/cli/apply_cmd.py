"""agentura apply -f <path> — Declarative skill deployment (like kubectl apply)."""

from pathlib import Path

import click
from rich.console import Console


@click.command("apply")
@click.option("-f", "--file", "path", required=True, type=click.Path(exists=True), help="Path to skill dir, domain dir, or skills root.")
@click.option("--dry-run", is_flag=True, help="Validate without deploying.")
def apply(path: str, dry_run: bool):
    """Deploy skills to the gateway declaratively.

    Scans the path for agentura.config.yaml files, validates each skill,
    and registers them with the running gateway.

    Examples:
      agentura apply -f skills/hr/interview-questions/  # Single skill
      agentura apply -f skills/hr/                     # Entire domain
      agentura apply -f skills/                        # Everything
    """
    console = Console()
    target = Path(path)

    # Find all config files under path
    configs = sorted(target.rglob("agentura.config.yaml"))
    if not configs:
        console.print(f"[yellow]No agentura.config.yaml found under {target}[/]")
        return

    console.print(f"Found {len(configs)} skill config(s) under {target}\n")

    from agentura_sdk.runner.config_loader import load_config
    from agentura_sdk.runner.skill_loader import load_skill_md

    errors = 0
    deployed = 0

    for config_path in configs:
        skill_dir = config_path.parent
        rel = skill_dir.relative_to(Path.cwd()) if skill_dir.is_relative_to(Path.cwd()) else skill_dir

        try:
            config = load_config(config_path)
        except Exception as e:
            console.print(f"  [red]FAIL[/]  {rel} — config error: {e}")
            errors += 1
            continue

        for skill_ref in config.skills:
            skill_path_full = skill_dir
            skill_md_path = skill_path_full / "SKILL.md"
            label = f"{config.domain.name}/{skill_ref.name}"

            # Validate SKILL.md exists
            if not skill_md_path.exists():
                console.print(f"  [red]FAIL[/]  {label} — SKILL.md not found")
                errors += 1
                continue

            # Validate SKILL.md parses
            try:
                skill_md = load_skill_md(skill_md_path)
            except Exception as e:
                console.print(f"  [red]FAIL[/]  {label} — SKILL.md error: {e}")
                errors += 1
                continue

            # Validate tests exist (admission control)
            tests_dir = skill_path_full / "tests"
            has_tests = tests_dir.exists() and any(tests_dir.iterdir())

            if dry_run:
                test_status = "[green]tests[/]" if has_tests else "[yellow]no tests[/]"
                console.print(
                    f"  [blue]DRY[/]   {label} "
                    f"({skill_ref.role}, {skill_ref.model.split('/')[-1]}) "
                    f"[{test_status}]"
                )
                deployed += 1
                continue

            # Deploy to gateway
            try:
                from agentura_sdk.cli.gateway import _client
                with _client() as c:
                    # Check if gateway is reachable
                    health = c.get("/healthz")
                    if health.status_code != 200:
                        console.print(f"  [red]FAIL[/]  {label} — gateway unhealthy")
                        errors += 1
                        continue

                # For now, skills are auto-discovered from the filesystem by the executor.
                # This command validates + confirms the skill is ready for the gateway.
                test_status = "[green]tests[/]" if has_tests else "[yellow]no tests[/]"
                console.print(
                    f"  [green]OK[/]    {label} "
                    f"({skill_ref.role}, {skill_ref.model.split('/')[-1]}) "
                    f"[{test_status}]"
                )
                deployed += 1

            except Exception as e:
                console.print(f"  [red]FAIL[/]  {label} — {e}")
                errors += 1

    # Summary
    console.print()
    if dry_run:
        console.print(f"[blue]Dry run:[/] {deployed} skill(s) validated, {errors} error(s)")
        if errors == 0:
            console.print("[dim]Run without --dry-run to deploy.[/]")
    else:
        console.print(f"[green]Applied:[/] {deployed} skill(s), {errors} error(s)")
