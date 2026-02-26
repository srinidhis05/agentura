"""agentura run <domain>/<name> — Execute a skill locally via Pydantic AI."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel


def _find_skills_dir() -> str:
    """Walk up from CWD to find a 'skills/' directory or use env override."""
    import os

    override = os.environ.get("AGENTURA_SKILLS_DIR")
    if override:
        return override

    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / "skills"
        if candidate.is_dir():
            return str(candidate)
    return "skills"


def _load_service_context(repo: Path, task_desc: str | None, console: Console) -> dict:
    """Load .agentura/services/{name}/ knowledge + mapped skills into input_data."""
    repo = repo.resolve()
    name = repo.name

    # Find the service index directory
    index_dir = repo / ".agentura" / "services" / name
    if not index_dir.exists():
        console.print(f"[yellow]Warning: No index found at {index_dir}. Run: agentura index {repo}[/]")
        return {"repo_path": str(repo), "task": task_desc or ""}

    context: dict = {
        "repo_path": str(repo),
        "task": task_desc or "",
    }

    # Load knowledge files
    for key, filename in [
        ("service_context", "SERVICE.md"),
        ("modules_context", "MODULES.md"),
        ("api_context", "API_SURFACE.md"),
        ("test_context", "TEST_MAP.md"),
    ]:
        path = index_dir / filename
        if path.exists():
            context[key] = path.read_text()

    # Map expertise skills (lazy — only if AI_VELOCITY_DIR is set)
    try:
        from agentura_sdk.indexer.detectors import detect_tech_stack
        from agentura_sdk.indexer.skill_mapper import map_skills

        tech = detect_tech_stack(repo)
        task_type = _infer_task_type(task_desc or "")
        skills = map_skills(tech, task_type)
        if skills:
            context["expertise"] = "\n\n---\n\n".join(s.content for s in skills)
            console.print(f"[dim]Loaded {len(skills)} expertise skill(s): {', '.join(s.name for s in skills)}[/]")
    except Exception:
        pass

    return context


def _infer_task_type(task: str) -> str:
    """Infer task type from description for skill mapping."""
    lower = task.lower()
    if any(w in lower for w in ["test", "spec", "coverage"]):
        return "test"
    if any(w in lower for w in ["metric", "instrument", "prometheus", "observability"]):
        return "instrument"
    if any(w in lower for w in ["dashboard", "grafana", "datadog"]):
        return "dashboard"
    if any(w in lower for w in ["alert", "pager", "notify"]):
        return "alert"
    return "code"


@click.command()
@click.argument("skill_path")
@click.option("--input", "input_file", type=click.Path(exists=True), help="JSON input file.")
@click.option("--dry-run", is_flag=True, help="Validate without calling model.")
@click.option(
    "--skills-dir",
    type=click.Path(exists=True),
    default=None,
    help="Root directory for skills.",
)
@click.option("--model", "model_override", help="Override model from config.")
@click.option("--repo", "repo_path", type=click.Path(exists=True), help="Repository path for service-agent skill.")
@click.option("--task", "task_desc", help="Task description for service-agent skill.")
def run(skill_path: str, input_file: str | None, dry_run: bool, skills_dir: str | None, model_override: str | None, repo_path: str | None, task_desc: str | None):
    if skills_dir is None:
        skills_dir = _find_skills_dir()
        if not Path(skills_dir).exists():
            Console().print(f"[red]Error: skills directory not found. Set --skills-dir or AGENTURA_SKILLS_DIR.[/]")
            raise SystemExit(1)
    """Run a skill locally.

    SKILL_PATH should be domain/skill-name, e.g. hr/interview-questions.
    """
    console = Console()

    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name[/]")
        raise SystemExit(1)

    domain, skill_name = parts
    root = Path(skills_dir) / domain / skill_name

    if not root.exists():
        console.print(f"[red]Error: skill not found at {root}[/]")
        raise SystemExit(1)

    # Load config and skill
    from agentura_sdk.runner.config_loader import load_config
    from agentura_sdk.runner.skill_loader import load_skill_md
    from agentura_sdk.types import SkillContext

    config = load_config(root / "agentura.config.yaml")
    skill_md = load_skill_md(root / "SKILL.md")

    # Build input data
    input_data = {}
    if input_file:
        input_data = json.loads(Path(input_file).read_text())
    elif (root / "fixtures" / "sample_input.json").exists():
        input_data = json.loads((root / "fixtures" / "sample_input.json").read_text())
        console.print("[dim]Using fixtures/sample_input.json (no --input specified)[/]")

    # Inject service context when --repo is provided
    if repo_path:
        input_data.update(_load_service_context(Path(repo_path), task_desc, console))

    model = model_override or skill_md.metadata.model

    # Compose system prompt: WORKSPACE + DOMAIN + Reflexion + SKILL
    prompt_parts = []
    if skill_md.workspace_context:
        prompt_parts.append(skill_md.workspace_context)
    if skill_md.domain_context:
        prompt_parts.append(skill_md.domain_context)
    if skill_md.reflexion_context:
        prompt_parts.append(skill_md.reflexion_context)
    prompt_parts.append(skill_md.system_prompt)
    composed_prompt = "\n\n---\n\n".join(prompt_parts)

    ctx = SkillContext(
        skill_name=skill_md.metadata.name,
        domain=skill_md.metadata.domain,
        role=skill_md.metadata.role,
        model=model,
        system_prompt=composed_prompt,
        input_data=input_data,
    )

    if dry_run:
        console.print(Panel("[yellow]DRY RUN[/] — Validating without calling model"))
        console.print(f"  Skill: {ctx.skill_name}")
        console.print(f"  Domain: {ctx.domain}")
        console.print(f"  Role: {ctx.role}")
        console.print(f"  Model: {ctx.model}")
        if skill_md.workspace_context:
            console.print(f"  Workspace context: loaded (WORKSPACE.md)")
        else:
            console.print(f"  Workspace context: [dim]none (no WORKSPACE.md found)[/]")
        if skill_md.domain_context:
            console.print(f"  Domain context: loaded (DOMAIN.md)")
        else:
            console.print(f"  Domain context: [dim]none (no DOMAIN.md found)[/]")
        if skill_md.reflexion_context:
            console.print(f"  Reflexion entries: loaded (learned rules injected)")
        else:
            console.print(f"  Reflexion entries: [dim]none (no past corrections)[/]")
        console.print(f"  Prompt length: {len(ctx.system_prompt)} chars")
        console.print(f"  Input keys: {list(input_data.keys())}")
        if repo_path:
            console.print(f"  Repo: {repo_path}")
            console.print(f"  Task: {task_desc or '[dim]none[/]'}")
            if "service_context" in input_data:
                console.print(f"  Service context: loaded ({len(input_data['service_context'])} chars)")
            if "expertise" in input_data:
                console.print(f"  Expertise: loaded ({len(input_data['expertise'])} chars)")
        console.print("\n[green]Validation passed.[/] Run without --dry-run to execute.")
        return

    # Execute via local runner
    from agentura_sdk.runner.local_runner import execute_skill

    console.print(f"[cyan]Executing {skill_name}...[/]")
    result = asyncio.run(execute_skill(ctx))

    if result.success:
        console.print(Panel(JSON(json.dumps(result.output, indent=2)), title="[green]Output"))
    else:
        console.print(Panel(JSON(json.dumps(result.output, indent=2)), title="[red]Error"))

    console.print(f"\n  Model: {result.model_used}")
    console.print(f"  Cost: ${result.cost_usd:.4f}")
    console.print(f"  Latency: {result.latency_ms:.0f}ms")

    if result.reasoning_trace:
        console.print("\n[dim]Reasoning trace:[/]")
        for step in result.reasoning_trace:
            console.print(f"  - {step}")

    if result.route_to:
        console.print(f"\n[yellow]Routes to: {result.route_to}[/]")
