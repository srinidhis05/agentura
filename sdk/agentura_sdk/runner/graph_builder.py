"""
Codebase knowledge graph builder for Kotlin and Swift codebases.

Runs at executor startup (after repos are cloned) and writes a compact graph.json
to /data/.agentura/graphs/<codebase>/ that can be queried by the query_code_graph tool.

Token savings vs raw git: instead of 5-10 git calls to find "what touches
RemittanceViewModel", a single graph query returns the full caller/dependency
set from an in-memory index built once and reused across all requests.

Graph structure (graph.json):
  meta        – build timestamp, file count, language
  files       – per-file: package/module, class names, import list
  class_index – className → file path (fast lookup)
  callers     – className → [files that import it]
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language-specific regex patterns
# ---------------------------------------------------------------------------

_KOTLIN = {
    "ext": ".kt",
    "package": re.compile(r"^package\s+([\w.]+)", re.MULTILINE),
    "import": re.compile(r"^import\s+([\w.*]+)", re.MULTILINE),
    "class": re.compile(
        r"(?:^|\n)\s*(?:(?:open|abstract|sealed|data|inner|enum|annotation|value|inline)\s+)*"
        r"(?:class|object|interface)\s+(\w+)",
    ),
    "fun": re.compile(r"(?:^|\n)\s*(?:(?:private|protected|internal|public|override|suspend|inline)\s+)*fun\s+(\w+)\s*\("),
}

_SWIFT = {
    "ext": ".swift",
    "package": re.compile(r"^//\s*Module:\s*([\w.]+)", re.MULTILINE),  # not standard, best-effort
    "import": re.compile(r"^import\s+([\w.]+)", re.MULTILINE),
    "class": re.compile(
        r"(?:^|\n)\s*(?:(?:open|public|internal|private|fileprivate|final|@MainActor)\s+)*"
        r"(?:class|struct|enum|protocol|actor)\s+(\w+)",
    ),
    "fun": re.compile(r"(?:^|\n)\s*(?:(?:private|public|internal|fileprivate|override|@MainActor)\s+)*func\s+(\w+)\s*\("),
}

_LANG_BY_EXT = {".kt": _KOTLIN, ".swift": _SWIFT}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(repo_dir: str, codebase: str) -> dict:
    """Scan repo_dir and return a graph dict. Does not write to disk."""
    root = Path(repo_dir)
    lang_cfg = _KOTLIN if codebase == "android" else _SWIFT
    ext = lang_cfg["ext"]

    files: dict[str, dict] = {}
    class_index: dict[str, str] = {}   # short class name → file path
    fqn_index: dict[str, str] = {}     # fully-qualified name → file path
    callers: dict[str, list[str]] = {}  # class/fqn → [files that import it]

    # --- Pass 1: index all declarations ---
    for path in root.rglob(f"*{ext}"):
        rel = str(path.relative_to(root))
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        pkg_m = lang_cfg["package"].search(text)
        package = pkg_m.group(1) if pkg_m else ""

        imports = lang_cfg["import"].findall(text)
        classes = lang_cfg["class"].findall(text)
        functions = lang_cfg["fun"].findall(text)

        # Derive module from top-level directory
        parts = rel.split(os.sep)
        module = parts[0] if parts else ""

        files[rel] = {
            "package": package,
            "module": module,
            "classes": classes,
            "functions": functions[:20],  # cap to keep JSON lean
            "imports": imports,
        }

        for cls in classes:
            class_index[cls] = rel
            if package:
                fqn = f"{package}.{cls}"
                fqn_index[fqn] = rel

    # --- Pass 2: build caller index ---
    for rel, info in files.items():
        for imp in info["imports"]:
            # Try FQN match first, then short name from last segment
            target = fqn_index.get(imp)
            if not target:
                short = imp.rsplit(".", 1)[-1].replace("*", "").strip()
                target = class_index.get(short)
            if target and target != rel:
                callers.setdefault(imp, [])
                callers.setdefault(imp.rsplit(".", 1)[-1], [])
                callers[imp].append(rel)
                callers[imp.rsplit(".", 1)[-1]].append(rel)

    # Deduplicate caller lists
    callers = {k: sorted(set(v)) for k, v in callers.items()}

    return {
        "meta": {
            "codebase": codebase,
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "file_count": len(files),
            "language": "kotlin" if codebase == "android" else "swift",
        },
        "files": files,
        "class_index": class_index,
        "fqn_index": fqn_index,
        "callers": callers,
    }


def build_and_save(repo_dir: str, codebase: str, out_dir: str) -> str:
    """Build graph and write graph.json. Returns path to graph.json."""
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "graph.json")
    print(f"[graph:build] START codebase={codebase} repo={repo_dir}", flush=True)
    t0 = time.time()
    graph = build_graph(repo_dir, codebase)
    elapsed = time.time() - t0
    print(
        f"[graph:build] DONE codebase={codebase} files={graph['meta']['file_count']} "
        f"classes={len(graph['class_index'])} elapsed={elapsed:.1f}s output={out_path}",
        flush=True,
    )
    with open(out_path, "w") as f:
        json.dump(graph, f, separators=(",", ":"))
    size_kb = os.path.getsize(out_path) // 1024
    print(f"[graph:build] SAVED {out_path} ({size_kb}KB)", flush=True)
    return out_path


# ---------------------------------------------------------------------------
# Query engine  (used by the query_code_graph tool at runtime)
# ---------------------------------------------------------------------------

_GRAPH_CACHE: dict[str, dict] = {}
_GRAPH_MTIME: dict[str, float] = {}


def _branch_slug(branch: str) -> str:
    """Filesystem-safe slug for branch names (e.g. 'release/1.5' → 'release__1.5')."""
    return branch.replace("/", "__").replace(" ", "_")


def _graph_path(codebase: str, branch: str | None) -> str:
    if branch:
        return f"/data/.agentura/graphs/{codebase}/branches/{_branch_slug(branch)}/graph.json"
    return f"/data/.agentura/graphs/{codebase}/graph.json"


def _load_graph(codebase: str, branch: str | None = None) -> dict | None:
    path = _graph_path(codebase, branch)
    cache_key = f"{codebase}:{branch}" if branch else codebase
    if not os.path.exists(path):
        print(f"[graph:load] MISS key={cache_key} path={path} (not found)", flush=True)
        return None
    mtime = os.path.getmtime(path)
    if _GRAPH_MTIME.get(cache_key) != mtime:
        size_kb = os.path.getsize(path) // 1024
        print(f"[graph:load] LOAD key={cache_key} size={size_kb}KB path={path}", flush=True)
        with open(path) as f:
            _GRAPH_CACHE[cache_key] = json.load(f)
        _GRAPH_MTIME[cache_key] = mtime
        meta = _GRAPH_CACHE[cache_key].get("meta", {})
        print(
            f"[graph:load] CACHED key={cache_key} files={meta.get('file_count')} "
            f"classes={len(_GRAPH_CACHE[cache_key].get('class_index', {}))} "
            f"built_at={meta.get('built_at')}",
            flush=True,
        )
    else:
        print(f"[graph:load] HIT key={cache_key} (serving from cache)", flush=True)
    return _GRAPH_CACHE.get(cache_key)


def query(codebase: str, mode: str, term: str, target: str = "", branch: str | None = None) -> str:
    """
    Query modes:
      find      – find files/classes matching term (name or keyword)
      callers   – who imports/references this class?
      deps      – what does this file/class depend on?
      module    – list all files in this module/directory
      summary   – high-level graph stats

    Tries graphify CLI first if installed (richer semantic queries),
    then falls back to the built-in index.
    """
    graph_file = _graph_path(codebase, branch)
    print(f"[graph:query] REQUEST codebase={codebase} branch={branch} mode={mode} term={term!r}", flush=True)

    # graphify CLI only operates on the default-branch graph — skip it if a
    # specific branch was requested, otherwise its results would be off-branch.
    if branch is None and mode in ("find", "callers") and os.path.exists(graph_file):
        print(f"[graph:query] TRYING graphify CLI for mode={mode} term={term!r}", flush=True)
        graphify_result = _load_graphify_for_query(codebase, mode, term)
        if graphify_result:
            print(f"[graph:query] SERVED_BY graphify len={len(graphify_result)}", flush=True)
            return graphify_result
        print(f"[graph:query] graphify returned nothing — falling back to built-in index", flush=True)

    graph = _load_graph(codebase, branch)
    if graph is None:
        if branch:
            return (
                f"[graph] No prebuilt graph for branch '{branch}' in '{codebase}'.\n"
                "RECOMMENDED FIRST MOVE for feature-branch questions: use git_codebase "
                f"with this command to see what's new/changed on the branch vs main:\n"
                f"  git diff --name-status origin/main..origin/{branch}\n"
                "(or substitute 'develop' for 'main' if the repo uses develop). "
                "This tells you which directories/files are NEW on this branch — focus "
                "exploration there. Do NOT start by globbing file names; the diff is "
                "the authoritative view of what the branch is actually about."
            )
        return (
            f"[graph] No graph found for '{codebase}'. "
            "It may still be building at startup (check executor logs). "
            "Fall back to git_codebase tool in the meantime."
        )

    files = graph.get("files", {})
    class_index = graph.get("class_index", {})
    callers = graph.get("callers", {})
    meta = graph.get("meta", {})

    if mode == "summary":
        return json.dumps({
            "codebase": codebase,
            "built_at": meta.get("built_at"),
            "file_count": meta.get("file_count"),
            "class_count": len(class_index),
            "hint": "Use mode=find to locate classes, mode=callers to find who uses them.",
        }, indent=2)

    if mode == "find":
        term_lower = term.lower()
        results = []
        for path, info in files.items():
            score = 0
            if term_lower in path.lower():
                score += 3
            for cls in info.get("classes", []):
                if term_lower in cls.lower():
                    score += 5
            for fn in info.get("functions", []):
                if term_lower in fn.lower():
                    score += 2
            if score > 0:
                results.append({
                    "file": path,
                    "module": info.get("module"),
                    "classes": info.get("classes"),
                    "score": score,
                })
        results.sort(key=lambda r: -r["score"])
        if not results:
            print(f"[graph:query] RESULT mode=find term={term!r} hits=0 SERVED_BY=builtin", flush=True)
            return f"[graph] No files found matching '{term}' in {codebase} codebase."
        print(f"[graph:query] RESULT mode=find term={term!r} hits={len(results)} top={results[0]['file']} SERVED_BY=builtin", flush=True)
        return json.dumps(results[:20], indent=2)

    if mode == "callers":
        hits = callers.get(term, [])
        if not hits:
            matches = [k for k in callers if term.lower() in k.lower()]
            if matches:
                best = matches[0]
                hits = callers[best]
                term = best
        if not hits:
            print(f"[graph:query] RESULT mode=callers term={term!r} hits=0 SERVED_BY=builtin", flush=True)
            return f"[graph] No callers found for '{term}' in {codebase} codebase."
        result = {
            "class": term,
            "caller_count": len(hits),
            "callers": hits[:30],
        }
        print(f"[graph:query] RESULT mode=callers term={term!r} callers={len(hits)} SERVED_BY=builtin", flush=True)
        return json.dumps(result, indent=2)

    if mode == "deps":
        # Find what a file/class depends on
        # Resolve term to a file path
        file_path = class_index.get(term) or (term if term in files else None)
        if not file_path:
            # Try partial path match
            matches = [p for p in files if term.lower() in p.lower()]
            file_path = matches[0] if matches else None
        if not file_path or file_path not in files:
            return f"[graph] Could not resolve '{term}' to a file in {codebase} codebase."
        info = files[file_path]
        imports = info.get("imports", [])
        # Resolve which imports map to local files
        local_deps = []
        for imp in imports:
            local = graph.get("fqn_index", {}).get(imp) or class_index.get(imp.rsplit(".", 1)[-1])
            if local:
                local_deps.append({"import": imp, "file": local})
        return json.dumps({
            "file": file_path,
            "module": info.get("module"),
            "classes": info.get("classes"),
            "local_dependencies": local_deps[:20],
            "all_imports": imports[:30],
        }, indent=2)

    if mode == "module":
        term_lower = term.lower()
        matches = {
            path: {"classes": info.get("classes"), "package": info.get("package")}
            for path, info in files.items()
            if path.lower().startswith(term_lower) or info.get("module", "").lower() == term_lower
        }
        if not matches:
            return f"[graph] No files found in module/path '{term}'."
        return json.dumps({
            "module": term,
            "file_count": len(matches),
            "files": dict(list(matches.items())[:30]),
        }, indent=2)

    return f"[graph] Unknown mode '{mode}'. Use: find, callers, deps, module, summary."


# ---------------------------------------------------------------------------
# Graphify integration (optional — used if installed)
# ---------------------------------------------------------------------------

_GRAPHIFY_OUT = {
    "android": "/codebase/vance-android/graphify-out",
    "ios":     "/codebase/vance-ios/graphify-out",
}

_GRAPHIFY_CMD = ["python3", "-m", "graphify"]


def _graphify_available() -> bool:
    try:
        import graphify  # noqa: F401
        return True
    except ImportError:
        return False


def _try_graphify(repo_dir: str, codebase: str) -> bool:
    """
    Run `python3 -m graphify update <repo>` to build the graph into
    <repo>/graphify-out/graph.json. Returns True on success.
    Falls back to the built-in builder if graphify is unavailable or fails.
    """
    import subprocess as sp

    if not _graphify_available():
        print("[graph:graphify] NOT INSTALLED — using built-in builder", flush=True)
        return False

    out_dir = _GRAPHIFY_OUT[codebase]
    graph_file = os.path.join(out_dir, "graph.json")
    print(f"[graph:graphify] BUILD START repo={repo_dir} out={out_dir}", flush=True)
    try:
        result = sp.run(
            _GRAPHIFY_CMD + ["update", repo_dir],
            capture_output=True, text=True, timeout=300, cwd=repo_dir,
        )
        if os.path.exists(graph_file):
            size_kb = os.path.getsize(graph_file) // 1024
            print(f"[graph:graphify] BUILD SUCCESS graph.json={size_kb}KB", flush=True)
            # Log key stats from output
            for line in result.stdout.splitlines():
                if "nodes" in line or "edges" in line or "communities" in line:
                    print(f"[graph:graphify] {line.strip()}", flush=True)
            return True
        print(f"[graph:graphify] BUILD FAILED — no graph.json at {graph_file}", flush=True)
        print(f"[graph:graphify] stdout={result.stdout[-400:]}", flush=True)
        print(f"[graph:graphify] stderr={result.stderr[-200:]}", flush=True)
    except sp.TimeoutExpired:
        print("[graph:graphify] BUILD TIMEOUT after 300s — falling back to built-in builder", flush=True)
    except Exception as exc:
        print(f"[graph:graphify] BUILD ERROR {exc} — falling back to built-in builder", flush=True)
    return False


def _load_graphify_for_query(codebase: str, mode: str, term: str) -> str | None:
    """
    Query the graphify graph using `python3 -m graphify query/path`.
    Returns the result string, or None if graphify is unavailable or returns nothing.
    """
    import subprocess as sp

    if not _graphify_available():
        print(f"[graph:graphify] query SKIP — not installed", flush=True)
        return None

    graph_file = os.path.join(_GRAPHIFY_OUT.get(codebase, ""), "graph.json")
    if not os.path.exists(graph_file):
        print(f"[graph:graphify] query SKIP — graph file not found at {graph_file}", flush=True)
        return None

    if mode == "callers":
        cmd = _GRAPHIFY_CMD + ["path", term, "--graph", graph_file]
    else:
        cmd = _GRAPHIFY_CMD + ["query", term, "--graph", graph_file, "--budget", "1500"]

    # Run from the repo root so graphify path/query find graphify-out/ by default
    repo_dir = os.path.dirname(os.path.dirname(graph_file))
    print(f"[graph:graphify] query CMD={' '.join(cmd)} cwd={repo_dir}", flush=True)
    try:
        result = sp.run(cmd, capture_output=True, text=True, timeout=30, cwd=repo_dir)
        output = (result.stdout or "").strip()
        if result.returncode != 0:
            print(f"[graph:graphify] query FAILED rc={result.returncode} stderr={result.stderr[:200]}", flush=True)
            return None
        if output:
            print(f"[graph:graphify] query OK len={len(output)} SERVED_BY=graphify", flush=True)
            return output[:6000]
        print(f"[graph:graphify] query EMPTY — no output", flush=True)
    except sp.TimeoutExpired:
        print(f"[graph:graphify] query TIMEOUT", flush=True)
    except Exception as exc:
        print(f"[graph:graphify] query ERROR {exc}", flush=True)
    return None


# ---------------------------------------------------------------------------
# CLI entry point (called from entrypoint.sh)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    codebase = sys.argv[1] if len(sys.argv) > 1 else "android"
    repo_map = {"android": "/codebase/vance-android", "ios": "/codebase/vance-ios"}
    repo_dir = repo_map.get(codebase)
    if not repo_dir or not os.path.isdir(repo_dir):
        print(f"[graph] repo not found for '{codebase}' at {repo_dir}", file=sys.stderr)
        sys.exit(1)
    out_dir = f"/data/.agentura/graphs/{codebase}"
    os.makedirs(out_dir, exist_ok=True)

    # Try graphify first (richer output); fall back to built-in builder
    if not _try_graphify(repo_dir, codebase):
        build_and_save(repo_dir, codebase, out_dir)
