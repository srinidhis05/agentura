"""agentura index <repo-path> — Index a service repository into markdown knowledge files."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console


@click.command("index")
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--name", "service_name", default=None, help="Service name (defaults to repo dir name).")
@click.option("--dry-run", is_flag=True, help="Detect tech stack only, no LLM calls.")
def index(repo_path: str, service_name: str | None, dry_run: bool):
    """Index a service repository into a markdown knowledge graph.

    Generates .agentura/services/{name}/ with SERVICE.md, MODULES.md,
    API_SURFACE.md, and TEST_MAP.md.
    """
    console = Console()
    repo = Path(repo_path).resolve()

    if dry_run:
        from agentura_sdk.indexer.generator import detect_only

        result = detect_only(repo)
        tech = result.tech_stack
        console.print(f"\n[cyan]Tech Stack Detection[/] — {repo.name}")
        console.print(f"  Languages:   {', '.join(tech.languages) or '[dim]none detected[/]'}")
        console.print(f"  Build tool:  {tech.build_tool or '[dim]none[/]'}")
        console.print(f"  Frameworks:  {', '.join(tech.frameworks) or '[dim]none[/]'}")
        console.print(f"  Test fw:     {tech.test_framework or '[dim]none[/]'}")
        console.print(f"  Pkg manager: {tech.package_manager or '[dim]none[/]'}")

        from agentura_sdk.indexer import detectors

        modules = detectors.map_modules(repo, tech)
        tests = detectors.find_test_files(repo, tech)
        api = detectors.find_api_surface(repo, tech)
        entries = detectors.find_entry_points(repo, tech)

        console.print(f"\n  Entry points: {len(entries)}")
        console.print(f"  Modules:      {len(modules)}")
        console.print(f"  Test files:   {len(tests)}")
        console.print(f"  API files:    {len(api)}")
        console.print("\n[green]Dry run complete.[/] Run without --dry-run to generate knowledge files.")
        return

    console.print(f"\n[cyan]Indexing {repo.name}...[/]")

    from agentura_sdk.indexer.generator import index_repository

    result = asyncio.run(index_repository(repo, service_name))

    console.print(f"\n[green]Indexed {result.service_name}[/]")
    console.print(f"  Output: {result.output_dir}")
    for f in result.files_generated:
        console.print(f"  [dim]→ {Path(f).name}[/]")
    console.print(f"\n  Languages: {', '.join(result.tech_stack.languages)}")
    console.print(f"  Build:     {result.tech_stack.build_tool}")
