"""Generator — orchestrates detectors + summarizer → writes knowledge markdown files.

Output: .agentura/services/{name}/ with SERVICE.md, MODULES.md, API_SURFACE.md, TEST_MAP.md
"""

from __future__ import annotations

from pathlib import Path

from agentura_sdk.indexer import detectors, summarizer
from agentura_sdk.types import ServiceIndex


async def index_repository(
    repo_path: Path,
    service_name: str | None = None,
) -> ServiceIndex:
    """Index a repository: detect stack → summarize with LLM → write markdown files."""
    repo = repo_path.resolve()
    name = service_name or repo.name

    # Phase 1: Static detection (no LLM)
    tech = detectors.detect_tech_stack(repo)
    entry_points = detectors.find_entry_points(repo, tech)
    test_files = detectors.find_test_files(repo, tech)
    api_files = detectors.find_api_surface(repo, tech)
    config_files = detectors.find_config_files(repo)
    modules = detectors.map_modules(repo, tech)

    # Phase 2: LLM summarization
    service_md = summarizer.summarize_service(repo, tech, entry_points, config_files)
    modules_md = summarizer.summarize_modules(repo, modules, tech)
    api_md = summarizer.summarize_api(repo, api_files, tech)
    test_md = summarizer.summarize_tests(repo, test_files, tech)

    # Phase 3: Write output
    output_dir = repo / ".agentura" / "services" / name
    output_dir.mkdir(parents=True, exist_ok=True)

    files_written: list[str] = []
    for filename, content in [
        ("SERVICE.md", service_md),
        ("MODULES.md", modules_md),
        ("API_SURFACE.md", api_md),
        ("TEST_MAP.md", test_md),
    ]:
        path = output_dir / filename
        path.write_text(content)
        files_written.append(str(path))

    return ServiceIndex(
        service_name=name,
        repo_path=str(repo),
        output_dir=str(output_dir),
        tech_stack=tech,
        files_generated=files_written,
    )


def detect_only(repo_path: Path) -> ServiceIndex:
    """Dry-run mode: detect tech stack without LLM calls."""
    repo = repo_path.resolve()
    tech = detectors.detect_tech_stack(repo)

    return ServiceIndex(
        service_name=repo.name,
        repo_path=str(repo),
        output_dir="",
        tech_stack=tech,
    )
