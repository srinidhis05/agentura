"""agentura create skill|agent <domain>/<name> — Scaffold skills and agents."""

import os
from datetime import date
from pathlib import Path

import click
from jinja2 import Environment, PackageLoader
from rich.console import Console

HANDLER_EXTENSIONS = {
    "python": ("handler.py", "handler.py.j2"),
    "typescript": ("handler.ts", "handler.ts.j2"),
    "go": ("handler.go", "handler.go.j2"),
}


AGENCY_DIR = Path(os.environ.get("AGENCY_DIR", "agency"))


@click.group()
def create():
    """Scaffold new skills, agents, and domains."""
    pass


@create.command("skill")
@click.argument("skill_path")
@click.option(
    "--lang",
    type=click.Choice(["python", "typescript", "go"]),
    default="python",
    help="Handler language (default: python).",
)
@click.option(
    "--role",
    type=click.Choice(["manager", "specialist", "field"]),
    default="specialist",
    help="Skill role (default: specialist).",
)
@click.option(
    "--skills-dir",
    type=click.Path(),
    default=None,
    help="Root directory for skills (default: skills/).",
)
def create_skill(skill_path: str, lang: str, role: str, skills_dir: str | None):
    if skills_dir is None:
        from agentura_sdk.cli.run import _find_skills_dir
        skills_dir = _find_skills_dir()
    """Create a new skill scaffold.

    SKILL_PATH should be domain/skill-name, e.g. hr/interview-questions.
    """
    console = Console()

    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name (e.g. hr/interview-questions)[/]")
        raise SystemExit(1)

    domain, skill_name = parts
    domain_root = Path(skills_dir) / domain
    root = domain_root / skill_name

    if root.exists():
        console.print(f"[red]Error: {root} already exists[/]")
        raise SystemExit(1)

    env = Environment(
        loader=PackageLoader("agentura_sdk", "templates"),
        keep_trailing_newline=True,
    )

    context = {
        "domain": domain,
        "skill_name": skill_name,
        "role": role,
        "lang": lang,
        "date": date.today().isoformat(),
    }

    # Create directory structure
    dirs = [root, root / "code", root / "tests", root / "fixtures"]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Domain-level files (only if this is the first skill in the domain)
    is_new_domain = not (domain_root / "DOMAIN.md").exists()
    domain_files = {}
    if is_new_domain:
        domain_files = {
            domain_root / "DOMAIN.md": "domain.md.j2",
            domain_root / "DECISIONS.md": "decisions.md.j2",
            domain_root / "GUARDRAILS.md": "guardrails.md.j2",
        }

    # Skill-level files
    skill_files = {
        root / "SKILL.md": "skill.md.j2",
        root / "agentura.config.yaml": "agentura.config.yaml.j2",
        root / "tests" / "test_deepeval.py": "test_deepeval.py.j2",
        root / "tests" / "test_promptfoo.yaml": "test_promptfoo.yaml.j2",
        root / "fixtures" / "sample_input.json": "sample_input.json.j2",
    }

    # Add language-specific handler
    handler_filename, handler_template = HANDLER_EXTENSIONS[lang]
    skill_files[root / "code" / handler_filename] = handler_template

    # Render all files
    all_files = {**domain_files, **skill_files}
    for filepath, template_name in all_files.items():
        template = env.get_template(template_name)
        filepath.write_text(template.render(**context))

    console.print(f"\n[green bold]Skill created:[/] {root}\n")

    if is_new_domain:
        console.print(f"[yellow]New domain:[/] {domain}")
        console.print("Domain files:")
        for filepath in sorted(domain_files.keys()):
            console.print(f"  {filepath.relative_to(domain_root.parent)}")
        console.print()

    console.print("Skill files:")
    for filepath in sorted(skill_files.keys()):
        console.print(f"  {filepath.relative_to(domain_root.parent)}")

    console.print(f"\n[cyan]Next steps:[/]")
    if is_new_domain:
        console.print(f"  1. Edit {domain_root}/DOMAIN.md — define domain identity, voice, and principles")
        console.print(f"  2. Edit {root}/SKILL.md — define your skill's task and output format")
        console.print(f"  3. Edit {root}/agentura.config.yaml — configure routing and guardrails")
    else:
        console.print(f"  1. Edit {root}/SKILL.md — define your skill's task and output format")
        console.print(f"  2. Edit {root}/agentura.config.yaml — configure routing and guardrails")
    console.print(f"  {'4' if is_new_domain else '3'}. agentura validate {skill_path}")
    console.print(f"  {'5' if is_new_domain else '4'}. agentura run {skill_path} --dry-run")
    console.print(f"  {'6' if is_new_domain else '5'}. agentura test {skill_path}")


@create.command("agent")
@click.argument("agent_path")
@click.option(
    "--role",
    type=click.Choice(["manager", "specialist", "field"]),
    default="specialist",
    help="Agent role (default: specialist).",
)
@click.option(
    "--executor",
    type=click.Choice(["claude-code", "ptc"]),
    default="claude-code",
    help="Executor type (default: claude-code).",
)
@click.option(
    "--model",
    default="anthropic/claude-sonnet-4-5-20250929",
    help="Model to use.",
)
@click.option(
    "--agency-dir",
    type=click.Path(),
    default=None,
    help="Root directory for agents (default: agency/).",
)
def create_agent(agent_path: str, role: str, executor: str, model: str, agency_dir: str | None):
    """Create a new agent scaffold.

    AGENT_PATH should be domain/agent-name, e.g. ecm/my-agent.
    """
    console = Console()

    parts = agent_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: agent path must be domain/name (e.g. ecm/my-agent)[/]")
        raise SystemExit(1)

    domain, agent_name = parts
    root_dir = Path(agency_dir) if agency_dir else AGENCY_DIR
    agent_dir = root_dir / domain / agent_name

    if agent_dir.exists():
        console.print(f"[red]Error: {agent_dir} already exists[/]")
        raise SystemExit(1)

    agent_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=PackageLoader("agentura_sdk", "templates"),
        keep_trailing_newline=True,
    )

    display_name = agent_name.replace("-", " ").title()
    context = {
        "domain": domain,
        "agent_name": agent_name,
        "display_name": display_name,
        "role": role,
        "executor": executor,
        "model": model,
    }

    files = {
        agent_dir / "agent.yaml": "agent.yaml.j2",
        agent_dir / "SOUL.md": "soul.md.j2",
    }

    for filepath, template_name in files.items():
        template = env.get_template(template_name)
        filepath.write_text(template.render(**context))

    console.print(f"\n[green bold]Agent created:[/] {agent_dir}\n")
    console.print("Files:")
    for filepath in sorted(files.keys()):
        console.print(f"  {filepath.relative_to(root_dir)}")

    console.print(f"\n[cyan]Next steps:[/]")
    console.print(f"  1. Edit {agent_dir}/agent.yaml — configure skills, budget, delegation")
    console.print(f"  2. Edit {agent_dir}/SOUL.md — define personality and working style")
    console.print(f"  3. Assign skills: add skill paths to the skills[] list in agent.yaml")
