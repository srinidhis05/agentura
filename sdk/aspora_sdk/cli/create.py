"""aspora create skill <domain>/<name> — Scaffold a new skill."""

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


@click.group()
def create():
    """Scaffold new skills and domains."""
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
    default="skills",
    help="Root directory for skills (default: skills/).",
)
def create_skill(skill_path: str, lang: str, role: str, skills_dir: str):
    """Create a new skill scaffold.

    SKILL_PATH should be domain/skill-name, e.g. wealth/suggest-allocation.
    """
    console = Console()

    parts = skill_path.strip("/").split("/")
    if len(parts) != 2:
        console.print("[red]Error: skill path must be domain/name (e.g. wealth/suggest-allocation)[/]")
        raise SystemExit(1)

    domain, skill_name = parts
    domain_root = Path(skills_dir) / domain
    root = domain_root / skill_name

    if root.exists():
        console.print(f"[red]Error: {root} already exists[/]")
        raise SystemExit(1)

    env = Environment(
        loader=PackageLoader("aspora_sdk", "templates"),
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
        root / "aspora.config.yaml": "aspora.config.yaml.j2",
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
        console.print(f"  3. Edit {root}/aspora.config.yaml — configure routing and guardrails")
    else:
        console.print(f"  1. Edit {root}/SKILL.md — define your skill's task and output format")
        console.print(f"  2. Edit {root}/aspora.config.yaml — configure routing and guardrails")
    console.print(f"  {'4' if is_new_domain else '3'}. aspora validate {skill_path}")
    console.print(f"  {'5' if is_new_domain else '4'}. aspora run {skill_path} --dry-run")
    console.print(f"  {'6' if is_new_domain else '5'}. aspora test {skill_path}")
