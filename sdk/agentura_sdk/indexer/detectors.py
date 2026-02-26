"""Static analysis detectors — pure functions, no LLM calls.

Each detector inspects the filesystem to extract structural information
about a service repository (tech stack, modules, tests, API surface).
"""

from __future__ import annotations

from pathlib import Path

from agentura_sdk.types import ModuleInfo, TechStack

# Marker file → (language, build_tool, package_manager) mappings
_STACK_MARKERS: list[tuple[str, str, str, str]] = [
    ("go.mod", "go", "go build", "go"),
    ("pom.xml", "java", "maven", "maven"),
    ("build.gradle", "java", "gradle", "gradle"),
    ("build.gradle.kts", "kotlin", "gradle", "gradle"),
    ("pyproject.toml", "python", "pip", "pip"),
    ("setup.py", "python", "pip", "pip"),
    ("package.json", "typescript", "npm", "npm"),
    ("Cargo.toml", "rust", "cargo", "cargo"),
]

_TEST_PATTERNS: dict[str, list[str]] = {
    "go": ["**/*_test.go"],
    "java": ["**/src/test/**/*.java", "**/*Test.java"],
    "python": ["**/test_*.py", "**/*_test.py", "**/tests/**/*.py"],
    "typescript": ["**/*.test.ts", "**/*.spec.ts", "**/*.test.tsx"],
    "kotlin": ["**/src/test/**/*.kt", "**/*Test.kt"],
    "rust": ["**/tests/**/*.rs"],
}

_TEST_FRAMEWORKS: dict[str, str] = {
    "go": "go test",
    "java": "junit",
    "python": "pytest",
    "typescript": "jest",
    "kotlin": "junit",
    "rust": "cargo test",
}

_API_PATTERNS: dict[str, list[str]] = {
    "go": ["**/handler*.go", "**/router*.go", "**/api*.go", "**/server*.go"],
    "java": ["**/*Controller.java", "**/*Resource.java", "**/*Endpoint.java"],
    "python": ["**/routes*.py", "**/views*.py", "**/api*.py", "**/endpoints*.py"],
    "typescript": ["**/routes*.ts", "**/controller*.ts", "**/api*.ts"],
}

_ENTRY_PATTERNS: dict[str, list[str]] = {
    "go": ["**/main.go", "**/cmd/**/main.go"],
    "java": ["**/*Application.java", "**/Main.java"],
    "python": ["**/main.py", "**/__main__.py", "**/app.py", "**/cli.py"],
    "typescript": ["**/index.ts", "**/main.ts", "**/app.ts"],
}

# Directories to skip during scanning
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "vendor", "target", "build", "dist", ".agentura"}


def detect_tech_stack(repo: Path) -> TechStack:
    """Detect languages, build tool, and package manager from marker files.

    Checks both root and one level deep (monorepo support).
    """
    languages: list[str] = []
    build_tool = ""
    package_manager = ""

    # Check root and immediate subdirectories for marker files
    search_dirs = [repo] + [d for d in repo.iterdir() if d.is_dir() and d.name not in _SKIP_DIRS and not d.name.startswith(".")]

    for search_dir in search_dirs:
        for marker, lang, tool, pm in _STACK_MARKERS:
            if (search_dir / marker).exists():
                if lang not in languages:
                    languages.append(lang)
                if not build_tool:
                    build_tool = tool
                    package_manager = pm

    primary = languages[0] if languages else ""
    test_fw = _TEST_FRAMEWORKS.get(primary, "")
    frameworks: list[str] = []
    for lang in languages:
        frameworks.extend(fw for fw in _detect_frameworks(repo, lang) if fw not in frameworks)

    return TechStack(
        languages=languages,
        build_tool=build_tool,
        frameworks=frameworks,
        test_framework=test_fw,
        package_manager=package_manager,
    )


def _detect_frameworks(repo: Path, language: str) -> list[str]:
    """Detect common frameworks from dependency files (checks root + subdirs)."""
    frameworks: list[str] = []

    # Collect all matching dependency files (root + one level deep)
    def _find_dep_file(name: str) -> list[Path]:
        found = []
        if (repo / name).exists():
            found.append(repo / name)
        for d in repo.iterdir():
            if d.is_dir() and d.name not in _SKIP_DIRS and (d / name).exists():
                found.append(d / name)
        return found

    if language == "python":
        for path in _find_dep_file("pyproject.toml"):
            text = path.read_text(errors="ignore").lower()
            for fw in ["fastapi", "flask", "django", "pydantic", "click"]:
                if fw in text and fw not in frameworks:
                    frameworks.append(fw)

    if language == "go":
        for path in _find_dep_file("go.mod"):
            text = path.read_text(errors="ignore")
            for fw, name in [("gin-gonic", "gin"), ("gorilla/mux", "gorilla-mux"), ("chi", "chi")]:
                if fw in text and name not in frameworks:
                    frameworks.append(name)

    if language == "typescript":
        for path in _find_dep_file("package.json"):
            text = path.read_text(errors="ignore").lower()
            for fw in ["next", "react", "express", "nestjs", "fastify"]:
                if f'"{fw}"' in text and fw not in frameworks:
                    frameworks.append(fw)

    if language == "java":
        for path in _find_dep_file("pom.xml"):
            text = path.read_text(errors="ignore")
            for fw in ["spring-boot", "quarkus", "micronaut"]:
                if fw in text and fw not in frameworks:
                    frameworks.append(fw)

    return frameworks


def find_entry_points(repo: Path, tech: TechStack) -> list[Path]:
    """Find main entry points for the primary language."""
    primary = tech.languages[0] if tech.languages else ""
    return _glob_patterns(repo, _ENTRY_PATTERNS.get(primary, []))


def find_test_files(repo: Path, tech: TechStack) -> list[Path]:
    """Find test files for the primary language."""
    primary = tech.languages[0] if tech.languages else ""
    return _glob_patterns(repo, _TEST_PATTERNS.get(primary, []))


def find_api_surface(repo: Path, tech: TechStack) -> list[Path]:
    """Find API endpoint/handler files."""
    primary = tech.languages[0] if tech.languages else ""
    return _glob_patterns(repo, _API_PATTERNS.get(primary, []))


def find_config_files(repo: Path) -> list[Path]:
    """Find configuration files (YAML, TOML, properties, env)."""
    patterns = ["**/*.yaml", "**/*.yml", "**/*.toml", "**/*.properties", "**/.env*", "**/Dockerfile*"]
    results = _glob_patterns(repo, patterns)
    return [f for f in results if not any(skip in f.parts for skip in _SKIP_DIRS)]


def map_modules(repo: Path, tech: TechStack) -> list[ModuleInfo]:
    """Map top-level logical modules (packages/directories)."""
    modules: list[ModuleInfo] = []
    primary = tech.languages[0] if tech.languages else ""

    # Language-specific source roots
    src_roots = _find_source_roots(repo, primary)

    for src in src_roots:
        if not src.is_dir():
            continue
        for child in sorted(src.iterdir()):
            if not child.is_dir() or child.name in _SKIP_DIRS or child.name.startswith("."):
                continue
            files = list(child.rglob("*"))
            source_files = [f for f in files if f.is_file() and not any(s in f.parts for s in _SKIP_DIRS)]
            lines = sum(_count_lines(f) for f in source_files)
            modules.append(ModuleInfo(
                path=str(child.relative_to(repo)),
                files_count=len(source_files),
                lines_count=lines,
            ))

    return modules


def _find_source_roots(repo: Path, language: str) -> list[Path]:
    """Determine source root directories based on language conventions."""
    if language == "java":
        roots = list(repo.glob("**/src/main/java"))
        return roots if roots else [repo]
    if language == "go":
        candidates = [repo / "cmd", repo / "internal", repo / "pkg"]
        return [c for c in candidates if c.is_dir()] or [repo]
    if language == "python":
        # Look for packages with __init__.py at depth 1
        candidates = [d for d in repo.iterdir() if d.is_dir() and (d / "__init__.py").exists()]
        return candidates if candidates else [repo]
    return [repo]


def _glob_patterns(repo: Path, patterns: list[str]) -> list[Path]:
    """Glob multiple patterns, deduplicate, filter skip dirs."""
    seen: set[Path] = set()
    results: list[Path] = []
    for pattern in patterns:
        for p in repo.glob(pattern):
            if p not in seen and not any(s in p.parts for s in _SKIP_DIRS):
                seen.add(p)
                results.append(p)
    return sorted(results)


def _count_lines(path: Path) -> int:
    """Count lines in a file, returning 0 on read errors."""
    try:
        return len(path.read_text(errors="ignore").splitlines())
    except (OSError, UnicodeDecodeError):
        return 0
