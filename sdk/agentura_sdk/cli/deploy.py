"""agentura deploy <domain>/<name> — Validate + sync skill to K8s executor pod.

Eliminates GR-006 (forgot kubectl cp) by combining validate + sync + restart
into a single command.
"""

import subprocess
from pathlib import Path

import click
from rich.console import Console


@click.command()
@click.argument("skill_path", required=False)
@click.option("--all", "deploy_all", is_flag=True, help="Deploy all skills.")
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default=None,
    help="Root directory for skills.",
)
@click.option(
    "--namespace",
    default="agentura",
    help="K8s namespace.",
)
@click.option(
    "--skip-validate",
    is_flag=True,
    help="Skip validation (not recommended).",
)
def deploy(skill_path: str | None, deploy_all: bool, skills_dir: str | None, namespace: str, skip_validate: bool):
    """Deploy skill(s) to K8s executor pod.

    SKILL_PATH should be domain/skill-name, e.g. dev/pr-code-reviewer.
    Use --all to deploy the entire skills directory.
    """
    console = Console()

    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()

    skills_root = Path(skills_dir)

    # Find executor pod
    pod_name = _get_executor_pod(namespace, console)
    if not pod_name:
        return

    if deploy_all:
        _deploy_directory(skills_root, skills_root, pod_name, namespace, skip_validate, console)
    elif skill_path:
        parts = skill_path.strip("/").split("/")
        if len(parts) != 2:
            console.print("[red]Error: skill path must be domain/name (e.g. dev/pr-code-reviewer)[/]")
            raise SystemExit(1)

        skill_dir = skills_root / parts[0] / parts[1]
        if not skill_dir.exists():
            console.print(f"[red]Error: skill not found at {skill_dir}[/]")
            raise SystemExit(1)

        _deploy_skill(skill_path, skill_dir, pod_name, namespace, skip_validate, console)
    else:
        console.print("[red]Error: provide a skill path or use --all[/]")
        raise SystemExit(1)


def _get_executor_pod(namespace: str, console: Console) -> str | None:
    """Find the executor pod name."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "pod", "-n", namespace, "-l", "app=executor",
             "-o", "jsonpath={.items[0].metadata.name}"],
            capture_output=True, text=True, timeout=10,
        )
        pod = result.stdout.strip()
        if not pod:
            console.print(f"[red]No executor pod found in namespace '{namespace}'[/]")
            console.print("[dim]Is the executor deployed? Run: kubectl get pods -n agentura[/]")
            return None
        return pod
    except FileNotFoundError:
        console.print("[red]kubectl not found. Is it installed and in PATH?[/]")
        return None
    except subprocess.TimeoutExpired:
        console.print("[red]kubectl timed out. Is the cluster reachable?[/]")
        return None


def _deploy_skill(skill_path: str, skill_dir: Path, pod_name: str, namespace: str, skip_validate: bool, console: Console):
    """Validate and deploy a single skill."""
    # Step 1: Validate
    if not skip_validate:
        console.print(f"[dim]Validating {skill_path}...[/]")
        from agentura_sdk.cli.validate import _validate_skill
        errors = _validate_skill(skill_path, str(skill_dir.parent.parent))
        if errors:
            console.print(f"[red]Validation failed — not deploying. Fix {len(errors)} error(s) first.[/]")
            raise SystemExit(1)

    # Step 2: kubectl cp
    remote_path = f"/skills/{skill_path}"
    console.print(f"[dim]Syncing {skill_path} → {pod_name}:{remote_path}[/]")
    result = subprocess.run(
        ["kubectl", "cp", str(skill_dir), f"{pod_name}:{remote_path}", "-n", namespace],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        console.print(f"[red]kubectl cp failed: {result.stderr}[/]")
        raise SystemExit(1)

    # Step 3: Verify
    verify = subprocess.run(
        ["kubectl", "exec", pod_name, "-n", namespace, "--",
         "ls", f"{remote_path}/SKILL.md"],
        capture_output=True, text=True, timeout=10,
    )
    if verify.returncode == 0:
        console.print(f"[green]Deployed {skill_path} to {pod_name}[/]")
    else:
        console.print(f"[red]Deploy may have failed — could not verify {remote_path}/SKILL.md[/]")


def _deploy_directory(skills_root: Path, local_root: Path, pod_name: str, namespace: str, skip_validate: bool, console: Console):
    """Deploy all skills in the skills directory."""
    console.print(f"[dim]Deploying all skills from {skills_root}...[/]")

    result = subprocess.run(
        ["kubectl", "cp", str(skills_root) + "/.", f"{pod_name}:/skills/", "-n", namespace],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        console.print(f"[red]kubectl cp failed: {result.stderr}[/]")
        raise SystemExit(1)

    console.print(f"[green]Deployed all skills to {pod_name}:/skills/[/]")


def _validate_skill(skill_path: str, skills_dir: str) -> list[str]:
    """Run validation and return list of errors (empty = valid).

    Lightweight version for deploy — doesn't print, just returns errors.
    """
    from pathlib import Path
    import yaml

    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        return [f"Invalid skill path: {skill_path}"]

    domain, skill_name = parts
    root = Path(skills_dir) / domain / skill_name

    errors = []

    if not (root / "SKILL.md").exists():
        errors.append("Missing SKILL.md")
    if not (root / "agentura.config.yaml").exists():
        errors.append("Missing agentura.config.yaml")
        return errors

    try:
        cfg_raw = yaml.safe_load((root / "agentura.config.yaml").read_text()) or {}
        for i, entry in enumerate(cfg_raw.get("mcp_tools", [])):
            if isinstance(entry, str):
                errors.append(f"mcp_tools[{i}] is string '{entry}' — must be dict (GR-018)")

        skills_list = cfg_raw.get("skills", [])
        role = skills_list[0].get("role", "specialist") if skills_list else "specialist"
        agent_section = cfg_raw.get("agent", {}) or cfg_raw.get("sandbox", {})
        if role == "agent" and not agent_section:
            errors.append("role=agent but no 'agent:' section")
    except Exception as e:
        errors.append(f"Invalid config: {e}")

    return errors
