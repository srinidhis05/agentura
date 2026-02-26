"""LLM-powered summarizer — generates markdown knowledge files from detected structure.

Uses Claude Haiku for cost efficiency (~$0.05 per full index).
"""

from __future__ import annotations

import os
from pathlib import Path

from anthropic import Anthropic

from agentura_sdk.types import ModuleInfo, TechStack

_MODEL = "claude-haiku-4-5-latest"
_MAX_FILE_PREVIEW = 3000  # chars per file preview sent to LLM


def _client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY required for summarization")
    return Anthropic(api_key=api_key)


def _read_preview(path: Path) -> str:
    """Read first N chars of a file for LLM context."""
    try:
        text = path.read_text(errors="ignore")
        return text[:_MAX_FILE_PREVIEW]
    except (OSError, UnicodeDecodeError):
        return ""


def _call_haiku(system: str, user: str) -> str:
    """Single Haiku call, return text content."""
    response = _client().messages.create(
        model=_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def summarize_service(
    repo: Path,
    tech: TechStack,
    entry_points: list[Path],
    config_files: list[Path],
) -> str:
    """Generate SERVICE.md — high-level service overview (< 5KB target)."""
    system = (
        "You generate concise SERVICE.md files for LLM consumption. "
        "Output markdown with these sections: Overview, Tech Stack, Entry Points, "
        "Build & Run, Key Configuration. Keep under 5KB. No filler."
    )

    entry_previews = "\n".join(
        f"### {p.relative_to(repo)}\n```\n{_read_preview(p)}\n```"
        for p in entry_points[:5]
    )
    config_list = "\n".join(f"- {p.relative_to(repo)}" for p in config_files[:10])

    user = f"""Service: {repo.name}
Languages: {', '.join(tech.languages)}
Build tool: {tech.build_tool}
Frameworks: {', '.join(tech.frameworks)}
Test framework: {tech.test_framework}
Package manager: {tech.package_manager}

Entry points:
{entry_previews}

Config files:
{config_list}

Generate SERVICE.md."""

    return _call_haiku(system, user)


def summarize_modules(
    repo: Path,
    modules: list[ModuleInfo],
    tech: TechStack,
) -> str:
    """Generate MODULES.md — module-level breakdown."""
    system = (
        "You generate concise MODULES.md files. For each module, describe its purpose "
        "based on the file listing and any key files shown. Use a table format. Keep under 3KB."
    )

    module_sections: list[str] = []
    for mod in modules[:20]:
        mod_path = repo / mod.path
        # List top-level files in the module
        if mod_path.is_dir():
            files = sorted(f.name for f in mod_path.iterdir() if f.is_file())[:10]
        else:
            files = []
        module_sections.append(
            f"### {mod.path}\n"
            f"Files: {mod.files_count}, Lines: {mod.lines_count}\n"
            f"Contents: {', '.join(files)}"
        )

    user = f"""Service: {repo.name} ({', '.join(tech.languages)})

Modules:
{chr(10).join(module_sections)}

Generate MODULES.md with a table: Module | Purpose | Size | Key Files."""

    return _call_haiku(system, user)


def summarize_api(
    repo: Path,
    api_files: list[Path],
    tech: TechStack,
) -> str:
    """Generate API_SURFACE.md — endpoints and handlers."""
    system = (
        "You generate concise API_SURFACE.md files listing API endpoints/handlers. "
        "Include: Method, Path, Handler, Description. Keep under 3KB."
    )

    api_previews = "\n".join(
        f"### {p.relative_to(repo)}\n```\n{_read_preview(p)}\n```"
        for p in api_files[:8]
    )

    user = f"""Service: {repo.name} ({', '.join(tech.languages)})

API handler files:
{api_previews}

Generate API_SURFACE.md with a table of endpoints."""

    if not api_files:
        return "# API Surface\n\nNo API endpoints detected.\n"

    return _call_haiku(system, user)


def summarize_tests(
    repo: Path,
    test_files: list[Path],
    tech: TechStack,
) -> str:
    """Generate TEST_MAP.md — test coverage map."""
    system = (
        "You generate concise TEST_MAP.md files mapping test files to what they test. "
        "Include: Test File, Tests, Framework. Keep under 2KB."
    )

    test_list = "\n".join(f"- {p.relative_to(repo)}" for p in test_files[:30])

    user = f"""Service: {repo.name}
Test framework: {tech.test_framework}

Test files:
{test_list}

Generate TEST_MAP.md with a table: Test File | What It Tests | Framework."""

    if not test_files:
        return "# Test Map\n\nNo test files detected.\n"

    return _call_haiku(system, user)
