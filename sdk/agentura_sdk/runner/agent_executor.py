"""Multi-turn agent executor with provider abstraction.

Supports OpenRouter (primary) and Anthropic SDK (fallback) for tool calling.
Provider selected via env vars: OPENROUTER_API_KEY first, ANTHROPIC_API_KEY second.
Sandbox backend selected via SANDBOX_BACKEND env var (docker | k8s).
MCP tools discovered dynamically from ctx.mcp_bindings.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path

from agentura_sdk.sandbox import get_sandbox_module
from agentura_sdk.types import AgentIteration, SandboxConfig, SkillContext, SkillResult

logger = logging.getLogger(__name__)

sandbox_mod = get_sandbox_module()

# Tool definitions in Anthropic format (canonical)
SANDBOX_TOOLS = [
    {
        "name": "write_file",
        "description": "Write content to a file in the sandbox filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path in the sandbox"},
                "content": {"type": "string", "description": "File content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file from the sandbox filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "run_command",
        "description": "Run a shell command in the sandbox (e.g. npm install, pip install, ls, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "run_code",
        "description": "Execute Python code in the sandbox and return the output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "clone_repo",
        "description": "Clone a git repository into the sandbox. Uses --depth 1 for speed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "Git repository URL (HTTPS or SSH)"},
                "branch": {"type": "string", "description": "Branch to clone (default: main)"},
                "target_dir": {"type": "string", "description": "Directory to clone into (default: /home/user/repo)"},
            },
            "required": ["repo_url"],
        },
    },
    {
        "name": "create_branch",
        "description": "Create and checkout a new git branch in a repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch_name": {"type": "string", "description": "Name for the new branch"},
                "base_dir": {"type": "string", "description": "Repository directory (default: /home/user/repo)"},
            },
            "required": ["branch_name"],
        },
    },
    {
        "name": "create_pr",
        "description": "Stage all changes, commit, push, and create a GitHub PR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "PR title (conventional commit format)"},
                "body": {"type": "string", "description": "PR body in markdown"},
                "base_dir": {"type": "string", "description": "Repository directory (default: /home/user/repo)"},
            },
            "required": ["title", "body"],
        },
    },
    {
        "name": "query_code_graph",
        "description": (
            "Query the pre-built codebase knowledge graph. PREFER THIS over git_codebase "
            "for broad questions — it returns structured relationship data in one call "
            "instead of many git round-trips, saving significant context tokens.\n\n"
            "Modes:\n"
            "  find    – locate files/classes by name or keyword\n"
            "  callers – find every file that imports/references a class\n"
            "  deps    – show what a file/class depends on\n"
            "  module  – list all files in a module or directory\n"
            "  summary – graph stats (file count, build time)\n\n"
            "Examples:\n"
            "  {mode:'find',    term:'RemittanceViewModel'}   → files containing this class\n"
            "  {mode:'callers', term:'RemittanceViewModel'}   → files that import it\n"
            "  {mode:'deps',    term:'RemittanceViewModel'}   → what it depends on\n"
            "  {mode:'module',  term:'data-layer'}            → all files in that module\n"
            "Fall back to git_codebase for authorship, blame, and recent-change queries. "
            "If the user asks about a non-default branch, pass it via the 'branch' param — "
            "the graph may not be prebuilt for that branch, in which case use git_codebase "
            "(which also accepts 'branch' and will check it out)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["find", "callers", "deps", "module", "summary"],
                    "description": "Query mode",
                },
                "term": {
                    "type": "string",
                    "description": "Class name, file path fragment, or keyword to query",
                },
                "codebase": {
                    "type": "string",
                    "description": "Which codebase: 'android' (default) or 'ios'",
                },
                "branch": {
                    "type": "string",
                    "description": (
                        "Optional branch name (can be partial/fuzzy — e.g. 'release 1.5' "
                        "resolves to 'release/1.5.0'). Omit for default branch."
                    ),
                },
            },
            "required": ["mode", "term"],
        },
    },
    {
        "name": "git_codebase",
        "description": (
            "Run a read-only git command against a mounted codebase. "
            "Use for: authorship (git log/blame), recent changes (git log), "
            "exact file content (git show). "
            "For finding files and class relationships, prefer query_code_graph — it's faster. "
            "Supported sub-commands: log, blame, show, diff, shortlog, ls-files, grep. "
            "Android source files live under app/src/main/java/ (not kotlin/). "
            "To get author: 'git log --follow -1 --format=\"%an\" -- <path>'. "
            "To blame a file: 'git blame <path>'. "
            "To see contributors: 'git shortlog -sne --all | head -20'. "
            "If the user mentions a branch (even partially, like 'release 1.5'), pass it "
            "via the 'branch' param — it'll be fuzzy-matched against remote branches and "
            "checked out under a lock before the command runs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Full git command to run, e.g. 'git blame path/to/File.kt'",
                },
                "codebase": {
                    "type": "string",
                    "description": "Which codebase to query: 'android' (default) or 'ios'",
                },
                "branch": {
                    "type": "string",
                    "description": (
                        "Optional branch name (can be partial/fuzzy). Triggers a fetch + "
                        "checkout under a cross-process lock before the command runs. "
                        "Omit to query the currently-checked-out branch."
                    ),
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "task_complete",
        "description": "Signal that the task is finished. Provide a summary of what was built and any output URLs or file paths.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Summary of what was accomplished"},
                "files_created": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of key files created",
                },
                "url": {"type": "string", "description": "Preview/staging URL if applicable"},
            },
            "required": ["summary"],
        },
    },
]


def _to_openai_tools(anthropic_tools: list[dict]) -> list[dict]:
    """Convert Anthropic-format tool defs to OpenAI-format for OpenRouter."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in anthropic_tools
    ]


def _build_tool_set(
    mcp_bindings: list[dict],
) -> tuple[list[dict], dict[str, str]]:
    """Build the full tool set: sandbox tools + MCP tools from bindings.

    Returns (anthropic_tools, tool_name→server_url map for MCP dispatch).
    """
    from agentura_sdk.mcp.client import fetch_tool_definitions

    all_tools = list(SANDBOX_TOOLS)
    tool_server_map: dict[str, str] = {}

    for binding in mcp_bindings:
        server_url = binding.get("url", "")
        requested_tools = binding.get("tools", [])
        if not server_url:
            logger.warning("MCP binding missing url: %s", binding)
            continue

        try:
            remote_tools = fetch_tool_definitions(server_url)
        except Exception as exc:
            logger.error("failed to fetch tools from %s: %s", server_url, exc)
            continue

        for tool_def in remote_tools:
            name = tool_def["name"]
            if requested_tools and name not in requested_tools:
                continue
            all_tools.append(tool_def)
            tool_server_map[name] = server_url

    return all_tools, tool_server_map


# --- Provider abstraction ---
# Normalized call result: (wants_tool_use, tool_calls[(id, name, args)], text, tokens_in, tokens_out)
_CallResult = tuple[bool, list[tuple[str, str, dict]], str, int, int]


class _OpenRouterProvider:
    """OpenAI-compatible tool calling via OpenRouter."""

    def __init__(self, model_id: str, system_prompt: str, tools: list[dict],
                 max_tokens: int = 16384, budget_tokens: int = 0):
        from agentura_sdk.runner.openrouter import resolve_model
        self._model = resolve_model(model_id)
        self._messages: list[dict] = [{"role": "system", "content": system_prompt}]
        self._tools = _to_openai_tools(tools)
        self._max_tokens = max_tokens
        self._budget_tokens = budget_tokens

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def call(self) -> _CallResult:
        from agentura_sdk.runner.openrouter import tool_chat_completion
        resp = tool_chat_completion(self._model, self._messages, self._tools,
                                    max_tokens=self._max_tokens, budget_tokens=self._budget_tokens)

        # Build assistant message for history
        assistant_msg: dict = {"role": "assistant"}
        if resp.content:
            assistant_msg["content"] = resp.content
        if resp.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                }
                for tc in resp.tool_calls
            ]
        self._messages.append(assistant_msg)

        wants_tools = bool(resp.tool_calls)
        calls = [(tc.id, tc.name, tc.arguments) for tc in resp.tool_calls]
        return wants_tools, calls, resp.content or "", resp.tokens_in, resp.tokens_out

    def add_tool_results(self, results: list[tuple[str, str]]) -> None:
        for call_id, output in results:
            self._messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": output,
            })


class _AnthropicProvider:
    """Anthropic Messages API tool calling."""

    def __init__(self, model_id: str, system_prompt: str, api_key: str, tools: list[dict],
                 max_tokens: int = 16384, budget_tokens: int = 0):
        from anthropic import Anthropic
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        self._client = Anthropic(api_key=api_key, base_url=base_url) if base_url else Anthropic(api_key=api_key)
        self._model = model_id
        self._system = system_prompt
        self._messages: list[dict] = []
        self._tools = tools
        self._max_tokens = max_tokens
        self._budget_tokens = budget_tokens

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def call(self) -> _CallResult:
        kwargs: dict = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "system": self._system,
            "tools": self._tools,
            "messages": self._messages,
        }
        if self._budget_tokens > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": self._budget_tokens,
            }
            logger.info("Extended thinking enabled (budget_tokens=%d)", self._budget_tokens)

        response = self._client.messages.create(**kwargs)

        assistant_content = response.content
        self._messages.append({"role": "assistant", "content": assistant_content})

        wants_tools = response.stop_reason == "tool_use"
        text_parts = [b.text for b in assistant_content if getattr(b, "type", "") == "text"]
        calls = [(b.id, b.name, b.input) for b in assistant_content if getattr(b, "type", "") == "tool_use"]

        tokens_in = getattr(response.usage, "input_tokens", 0)
        tokens_out = getattr(response.usage, "output_tokens", 0)

        return wants_tools, calls, "\n".join(text_parts), tokens_in, tokens_out

    def add_tool_results(self, results: list[tuple[str, str]]) -> None:
        tool_results = [
            {"type": "tool_result", "tool_use_id": call_id, "content": output}
            for call_id, output in results
        ]
        self._messages.append({"role": "user", "content": tool_results})


def _resolve_anthropic_model(model: str) -> str:
    """Resolve model string to Anthropic model ID."""
    name = model.removeprefix("anthropic/")
    aliases = {
        "claude-sonnet-4.5": "claude-sonnet-4-6",
        "claude-sonnet-4-5": "claude-sonnet-4-6",
        "claude-haiku-4.5": "claude-haiku-4-5",
        "claude-haiku-4-5": "claude-haiku-4-5",
        "claude-opus-4.6": "claude-opus-4-6",
    }
    return aliases.get(name, name)


def _is_anthropic_model(model: str) -> bool:
    """Check if the model is an Anthropic Claude model."""
    return model.startswith("anthropic/") or "claude" in model.lower()


def _get_provider(
    model: str,
    system_prompt: str,
    tools: list[dict],
    max_tokens: int = 16384,
    budget_tokens: int = 0,
) -> _OpenRouterProvider | _AnthropicProvider:
    """Select provider: Anthropic direct for Claude models, OpenRouter for others."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key and _is_anthropic_model(model):
        model_id = _resolve_anthropic_model(model)
        logger.info("Using Anthropic provider for %s (resolved: %s, max_tokens=%d, budget_tokens=%d)",
                     model, model_id, max_tokens, budget_tokens)
        return _AnthropicProvider(model_id, system_prompt, api_key, tools,
                                  max_tokens=max_tokens, budget_tokens=budget_tokens)

    if os.environ.get("OPENROUTER_API_KEY"):
        logger.info("Using OpenRouter provider for %s (max_tokens=%d, budget_tokens=%d)",
                     model, max_tokens, budget_tokens)
        return _OpenRouterProvider(model, system_prompt, tools, max_tokens=max_tokens, budget_tokens=budget_tokens)

    if api_key:
        model_id = _resolve_anthropic_model(model)
        logger.info("Using Anthropic provider (fallback) for %s (resolved: %s)", model, model_id)
        return _AnthropicProvider(model_id, system_prompt, api_key, tools,
                                  max_tokens=max_tokens, budget_tokens=budget_tokens)

    raise RuntimeError(
        "No LLM provider configured. Set ANTHROPIC_API_KEY (preferred for Claude) or OPENROUTER_API_KEY."
    )


# --- Tool execution ---

def _execute_tool(
    sandbox: object,
    tool_name: str,
    tool_input: dict,
    tool_server_map: dict[str, str],
) -> str:
    """Dispatch a tool call — MCP server first, then sandbox fallback."""
    # MCP tool dispatch
    server_url = tool_server_map.get(tool_name)
    if server_url:
        from agentura_sdk.mcp.client import call_tool
        return call_tool(server_url, tool_name, tool_input)

    # Sandbox tools
    if tool_name == "write_file":
        path = tool_input.get("path", "")
        content = tool_input.get("content", "")
        if not path:
            return "[error] write_file requires 'path' argument"
        return sandbox_mod.write_file(sandbox, path, content)
    if tool_name == "read_file":
        path = tool_input.get("path", "")
        if not path:
            return "[error] read_file requires 'path' argument"
        return sandbox_mod.read_file(sandbox, path)
    if tool_name == "run_command":
        cmd = tool_input.get("command", "")
        if not cmd:
            return "[error] run_command requires 'command' argument"
        return sandbox_mod.run_command(sandbox, cmd)
    if tool_name == "run_code":
        code = tool_input.get("code", "")
        if not code:
            return "[error] run_code requires 'code' argument"
        return sandbox_mod.run_code(sandbox, code)
    if tool_name == "clone_repo":
        return _clone_repo(sandbox, tool_input)
    if tool_name == "create_branch":
        return _create_branch(sandbox, tool_input)
    if tool_name == "create_pr":
        return _create_pr(sandbox, tool_input)
    if tool_name == "query_code_graph":
        return _query_code_graph(tool_input)
    if tool_name == "git_codebase":
        return _git_codebase(tool_input)
    if tool_name == "task_complete":
        return json.dumps(tool_input)
    return f"Unknown tool: {tool_name}"


def _query_code_graph(params: dict) -> str:
    """Dispatch to the graph query engine.

    If a branch is specified and no graph exists for it, build one on demand:
    acquire the repo lock, fuzzy-resolve the branch, check it out, run the
    built-in graph builder (~0.5s), then query. Subsequent queries on the
    same branch hit the cache.
    """
    from agentura_sdk.runner.graph_builder import query as graph_query
    mode = params.get("mode", "find")
    term = params.get("term", "").strip()
    codebase = params.get("codebase", "android").lower()
    branch = (params.get("branch") or "").strip() or None
    if not term and mode != "summary":
        return "[error] query_code_graph requires 'term'"

    resolution_note = ""
    if branch:
        resolved, err, note = _ensure_branch_graph(codebase, branch)
        if err:
            return err
        if resolved:
            branch = resolved
            resolution_note = note

    result = graph_query(codebase, mode, term, branch=branch)
    if resolution_note:
        result = f"{resolution_note}\n{result}"
    return result


def _ensure_branch_graph(codebase: str, branch: str) -> tuple[str | None, str | None, str]:
    """Build a branch-specific graph if missing. Returns (resolved_branch, error, note).

    On success: (resolved, None, note_or_empty) — note indicates fuzzy resolution
    or build-on-demand so the LLM can see what happened.
    On error:   (None, error_message, "")
    """
    import fcntl
    from agentura_sdk.runner.graph_builder import _graph_path, build_and_save

    repo_dir = _CODEBASE_ROOTS.get(codebase)
    if not repo_dir:
        return (None, f"[error] unknown codebase '{codebase}'", "")

    # Fast path: graph already exists for the raw input branch name
    if os.path.exists(_graph_path(codebase, branch)):
        return (branch, None, "")

    lock_path = _repo_lock_path(codebase)
    try:
        lock_fd = open(lock_path, "w")
    except OSError as exc:
        return (None, f"[error] could not open repo lock: {exc}", "")

    try:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)

        resolved, err = _resolve_branch(repo_dir, branch)
        if err:
            return (None, err, "")

        # Graph may exist under the resolved name (e.g. user typed fuzzy input)
        if os.path.exists(_graph_path(codebase, resolved)):
            note = (
                f"[branch: {resolved} (fuzzy-matched from '{branch}')]"
                if resolved != branch else ""
            )
            return (resolved, None, note)

        # Need to build. Checkout branch under the same lock, then scan.
        switch_err = _switch_branch(repo_dir, resolved)
        if switch_err:
            return (None, switch_err, "")

        out_dir = os.path.dirname(_graph_path(codebase, resolved))
        try:
            build_and_save(repo_dir, codebase, out_dir)
        except Exception as exc:
            return (None, f"[error] graph build failed: {exc}", "")

        if resolved != branch:
            note = (
                f"[branch: {resolved} (graph built on demand, "
                f"fuzzy-matched from '{branch}')]"
            )
        else:
            note = f"[branch: {resolved} (graph built on demand)]"
        return (resolved, None, note)
    finally:
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        lock_fd.close()


_CODEBASE_ROOTS = {
    "android": "/codebase/vance-android",
    "ios": "/codebase/vance-ios",
}

_GIT_ALLOWED_SUBCMDS = {"log", "blame", "show", "diff", "shortlog", "ls-files", "grep"}

# Cache remote-branch listings per repo — avoids hitting the network on every
# branch resolution. TTL is deliberately short so newly-pushed branches surface
# within a minute.
_BRANCH_LIST_CACHE: dict[str, tuple[float, list[str]]] = {}
_BRANCH_CACHE_TTL_S = 60.0


def _list_remote_branches(repo_dir: str) -> list[str]:
    """List branches on origin. Cached for _BRANCH_CACHE_TTL_S per repo."""
    import subprocess as sp
    now = time.monotonic()
    cached = _BRANCH_LIST_CACHE.get(repo_dir)
    if cached and now - cached[0] < _BRANCH_CACHE_TTL_S:
        return cached[1]
    try:
        result = sp.run(
            ["git", "ls-remote", "--heads", "origin"],
            cwd=repo_dir, capture_output=True, text=True, timeout=15,
        )
    except Exception:
        return cached[1] if cached else []
    if result.returncode != 0:
        return cached[1] if cached else []
    branches: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.strip().split("\t")
        if len(parts) == 2 and parts[1].startswith("refs/heads/"):
            branches.append(parts[1][len("refs/heads/"):])
    _BRANCH_LIST_CACHE[repo_dir] = (now, branches)
    return branches


def _resolve_branch(repo_dir: str, user_input: str) -> tuple[str | None, str | None]:
    """Fuzzy-match user input against remote branches.

    Returns (resolved_branch, error). Exactly one is non-None.

    Resolution order:
      1. Exact match (case-sensitive)
      2. Case-insensitive exact match
      3. Single substring match
      4. Top difflib candidate with ratio >= 0.9 AND clear lead over runner-up
      5. Otherwise: ambiguous — return candidate list for disambiguation
    """
    from difflib import SequenceMatcher, get_close_matches

    user_input = (user_input or "").strip()
    if not user_input:
        return None, "[error] empty branch name"

    branches = _list_remote_branches(repo_dir)
    if not branches:
        return None, "[error] could not list remote branches (network/auth issue?)"

    if user_input in branches:
        return user_input, None
    for b in branches:
        if b.lower() == user_input.lower():
            return b, None

    substr = [b for b in branches if user_input.lower() in b.lower()]
    if len(substr) == 1:
        return substr[0], None

    candidates = get_close_matches(user_input, branches, n=3, cutoff=0.5)
    if not candidates and substr:
        candidates = substr[:3]
    if not candidates:
        return None, f"[error] no branch found matching '{user_input}'"

    scores = sorted(
        ((c, SequenceMatcher(None, user_input.lower(), c.lower()).ratio()) for c in candidates),
        key=lambda x: -x[1],
    )
    top_name, top_score = scores[0]

    # Single candidate with decent confidence — auto-pick (handles typos like "mane" → "main")
    if len(scores) == 1 and top_score >= 0.7:
        return top_name, None

    # Multiple candidates but one clear winner
    if len(scores) >= 2:
        runner_up_score = scores[1][1]
        if top_score >= 0.9 and top_score - runner_up_score > 0.15:
            return top_name, None

    return None, (
        f"[ambiguous] branch '{user_input}' matches multiple candidates: "
        + ", ".join(f"'{c}'" for c, _ in scores)
        + ". Ask the user to specify the exact branch name, or retry with one of these."
    )


def _switch_branch(repo_dir: str, branch: str) -> str | None:
    """Fetch + checkout `branch` in `repo_dir`. Returns error string or None."""
    import subprocess as sp
    try:
        fetch = sp.run(
            ["git", "fetch", "--depth=500", "origin", f"{branch}:refs/remotes/origin/{branch}"],
            cwd=repo_dir, capture_output=True, text=True, timeout=60,
        )
        if fetch.returncode != 0:
            return f"[error] fetch failed for '{branch}': {fetch.stderr.strip()[:300]}"
        checkout = sp.run(
            ["git", "checkout", "-B", branch, f"origin/{branch}"],
            cwd=repo_dir, capture_output=True, text=True, timeout=15,
        )
        if checkout.returncode != 0:
            return f"[error] checkout failed for '{branch}': {checkout.stderr.strip()[:300]}"
        return None
    except sp.TimeoutExpired:
        return "[error] git fetch/checkout timed out"
    except Exception as exc:
        return f"[error] branch switch failed: {exc}"


def _repo_lock_path(codebase: str) -> str:
    lock_dir = "/data/.agentura/locks"
    os.makedirs(lock_dir, exist_ok=True)
    return os.path.join(lock_dir, f"{codebase}.branch.lock")


def _git_codebase(params: dict) -> str:
    """Run a read-only git command against a mounted codebase.

    If `branch` is supplied, fuzzy-resolve it against remote branches, then
    fetch + checkout under a cross-process file lock (required because uvicorn
    runs with multiple workers sharing the same repo clone). The lock is held
    through the git command itself so another worker can't switch branches
    mid-query.
    """
    import fcntl
    import shlex
    import subprocess as sp

    command = params.get("command", "").strip()
    codebase = params.get("codebase", "android").lower()
    requested_branch = (params.get("branch") or "").strip()

    repo_dir = _CODEBASE_ROOTS.get(codebase)
    if not repo_dir:
        return f"[error] unknown codebase '{codebase}'. Use 'android' or 'ios'."

    if not os.path.isdir(repo_dir):
        return f"[error] codebase not found at {repo_dir}"

    if not command:
        return "[error] empty command"

    if any(op in command for op in ("|", ";", "&&", "||", ">", "<", "`", "$(")):
        return "[error] shell operators are not allowed in git commands"

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return f"[error] could not parse command: {exc}"

    args = tokens[1:] if tokens and tokens[0] == "git" else tokens
    subcmd = args[0] if args else ""
    if not subcmd or subcmd not in _GIT_ALLOWED_SUBCMDS:
        return (
            f"[error] git sub-command '{subcmd}' is not allowed. "
            f"Allowed: {', '.join(sorted(_GIT_ALLOWED_SUBCMDS))}"
        )

    resolved_branch: str | None = None
    lock_path = _repo_lock_path(codebase)

    try:
        lock_fd = open(lock_path, "w")
    except OSError as exc:
        return f"[error] could not open repo lock at {lock_path}: {exc}"

    try:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)

        if requested_branch:
            resolved_branch, err = _resolve_branch(repo_dir, requested_branch)
            if err:
                return err
            switch_err = _switch_branch(repo_dir, resolved_branch)
            if switch_err:
                return switch_err

        git_argv = ["git"] + args
        try:
            result = sp.run(
                git_argv,
                cwd=repo_dir,
                shell=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = (result.stdout or "") + (result.stderr or "")
            output = output.strip() or "(no output)"
            if len(output) > 8000:
                output = output[:8000] + "\n... [truncated]"
            if resolved_branch:
                note = f"[branch: {resolved_branch}"
                if resolved_branch != requested_branch:
                    note += f" (fuzzy-matched from '{requested_branch}')"
                note += "]"
                output = f"{note}\n{output}"
            return output
        except sp.TimeoutExpired:
            return "[error] git command timed out after 30s"
        except Exception as exc:
            return f"[error] {exc}"
    finally:
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        lock_fd.close()


def _clone_repo(sandbox: object, params: dict) -> str:
    url = params["repo_url"]
    branch = params.get("branch", "main")
    target = params.get("target_dir", "/home/user/repo")
    cmd = f"git clone --depth 1 --branch {branch} {url} {target}"
    return sandbox_mod.run_command(sandbox, cmd)


def _create_branch(sandbox: object, params: dict) -> str:
    branch = params["branch_name"]
    base_dir = params.get("base_dir", "/home/user/repo")
    cmd = f"cd {base_dir} && git checkout -b {branch}"
    return sandbox_mod.run_command(sandbox, cmd)


def _create_pr(sandbox: object, params: dict) -> str:
    title = params["title"].replace('"', '\\"')
    body = params["body"].replace('"', '\\"')
    base_dir = params.get("base_dir", "/home/user/repo")
    cmd = (
        f'cd {base_dir} && git add -A && git commit -m "{title}" '
        f'&& git push -u origin HEAD '
        f'&& gh pr create --title "{title}" --body "{body}"'
    )
    return sandbox_mod.run_command(sandbox, cmd)


# --- Artifact extraction ---

def _extract_artifacts(sandbox: object, files_created: list[str], skill_name: str) -> tuple[str, dict]:
    """Extract files from sandbox to host /artifacts directory for downstream skills."""
    artifacts_dir = os.environ.get("ARTIFACTS_DIR", "/artifacts")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    output_dir = os.path.join(artifacts_dir, f"{skill_name}-{ts}")
    os.makedirs(output_dir, exist_ok=True)

    artifacts: dict[str, str] = {}
    for fpath in files_created:
        content = sandbox_mod.read_file(sandbox, fpath)
        if not content.startswith("[error]"):
            Path(output_dir, os.path.basename(fpath)).write_text(content)
            artifacts[fpath] = content

    return output_dir, artifacts


# --- Memory recall ---

def _recall_memories(skill_path: str, input_data: dict) -> str:
    """Search past corrections and reflexions for relevant context.

    Tries semantic search first. Falls back to direct DB lookups if
    vector search returns empty (common when embeddings fail).
    """
    try:
        from agentura_sdk.memory import get_memory_store

        store = get_memory_store()
        lines: list[str] = []

        # Try semantic search first
        query = json.dumps(input_data, default=str)[:500]
        results = store.search_similar(skill_path, query, limit=3)
        for r in results:
            text = r.get("memory", "") or r.get("rule", "") or r.get("user_correction", "")
            if text:
                lines.append(f"- {text[:300]}")

        # Fallback: load corrections and reflexions directly from store
        if not lines:
            try:
                corrections = store.get_corrections(skill_path)
                for c in corrections[:3]:
                    text = c.get("user_correction", c.get("correction", ""))
                    if text:
                        lines.append(f"- {text[:300]}")
            except Exception:
                pass
            try:
                # Prefer scope-aware retrieval (cross-agent learning)
                if hasattr(store, "get_top_reflexions_with_scope"):
                    reflexions = store.get_top_reflexions_with_scope(skill_path, limit=3, min_score=0.3)
                else:
                    reflexions = store.get_reflexions(skill_path)
                for r in reflexions[:3]:
                    text = r.get("rule", "")
                    if text:
                        lines.append(f"- {text[:300]}")
            except Exception:
                pass

        if not lines:
            return ""

        header = "## Memory — Learned Preferences from Past Executions\n"
        footer = "\nApply these learned preferences to the current task."
        return header + "\n".join(lines) + footer
    except Exception as exc:
        logger.debug("Memory recall skipped: %s", exc)
        return ""


def _inject_reflexions(skill_path: str) -> tuple[str, list[str]]:
    """Load top utility-scored reflexions for prompt injection.

    Returns (prompt_block, list_of_reflexion_ids) so the caller can
    record which reflexions were injected after the execution_id is known.
    """
    try:
        from agentura_sdk.memory import get_memory_store

        store = get_memory_store()
        reflexions = store.get_top_reflexions(skill_path, limit=5, min_score=0.3)
        if not reflexions:
            return "", []

        lines = []
        ids = []
        for r in reflexions:
            content = r.get("rule", "")
            score = r.get("utility_score", 0.5)
            rid = r.get("reflexion_id", "")
            if content:
                lines.append(f"- {content[:300]} (confidence: {score:.2f})")
                if rid:
                    ids.append(rid)

        if not lines:
            return "", []

        block = (
            "<past_learnings>\n"
            "These are patterns learned from previous reviews on this repo. "
            "Use them to calibrate your findings.\n"
            + "\n".join(lines)
            + "\n</past_learnings>"
        )
        logger.info("Injected %d reflexions into prompt for %s", len(ids), skill_path)
        return block, ids
    except Exception as exc:
        logger.debug("Reflexion injection skipped: %s", exc)
        return "", []


def _build_prompt_with_memory(ctx: SkillContext) -> tuple[str, list[str]]:
    """Compose system prompt with memory recall and reflexions injected.

    Returns (system_prompt, injected_reflexion_ids).
    """
    skill_path = f"{ctx.domain}/{ctx.skill_name}"

    # Inject utility-scored reflexions
    reflexion_block, reflexion_ids = _inject_reflexions(skill_path)

    # Recall general memories (corrections, etc.)
    memory_section = _recall_memories(skill_path, ctx.input_data)

    parts = []
    if reflexion_block:
        parts.append(reflexion_block)
    if memory_section:
        parts.append(memory_section)

    if parts:
        prefix = "\n\n---\n\n".join(parts)
        logger.info("Injected %d chars of memory+reflexion context", len(prefix))
        return f"{prefix}\n\n---\n\n{ctx.system_prompt}", reflexion_ids
    return ctx.system_prompt, reflexion_ids


# --- Agent loops ---

async def execute_agent(ctx: SkillContext) -> SkillResult:
    """Run the multi-turn agent loop: LLM tool calling → sandbox → iterate."""
    start = time.monotonic()
    config = ctx.sandbox_config or SandboxConfig()
    iterations: list[AgentIteration] = []

    # Build dynamic tool set (sandbox + MCP)
    all_tools, tool_server_map = _build_tool_set(ctx.mcp_bindings)
    if tool_server_map:
        logger.info("MCP tools loaded: %s", list(tool_server_map.keys()))

    # Compose prompt with memory recall + reflexion injection
    system_prompt, injected_reflexion_ids = _build_prompt_with_memory(ctx)

    try:
        provider = _get_provider(ctx.model, system_prompt, all_tools,
                                 max_tokens=config.max_tokens, budget_tokens=config.budget_tokens)
    except RuntimeError as e:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e)},
        )

    model_id = ctx.model
    sandbox = await sandbox_mod.create(config)

    try:
        provider.add_user_message(json.dumps(ctx.input_data, indent=2))
        final_output: dict = {}
        total_in = 0
        total_out = 0

        task_completed = False
        nudged = False
        write_counts: dict[str, int] = {}  # track write_file calls per path
        for i in range(config.max_iterations):
            wants_tools, tool_calls, text, tokens_in, tokens_out = await asyncio.to_thread(provider.call)
            total_in += tokens_in
            total_out += tokens_out

            if not wants_tools:
                if not iterations and not nudged:
                    # LLM responded with text without ever calling tools — nudge once.
                    nudged = True
                    logger.warning("Agent responded without tool use, nudging once")
                    provider.add_user_message(
                        "You MUST use the available tools to complete this task. "
                        "Do not respond with text only. Start by calling the appropriate tool."
                    )
                    continue
                final_output = {"summary": text}
                break

            results: list[tuple[str, str]] = []
            for call_id, name, args in tool_calls:
                # Detect write_file loops — reject writes after 2 to same path
                if name == "write_file":
                    fpath = args.get("path", "")
                    write_counts[fpath] = write_counts.get(fpath, 0) + 1
                    if write_counts[fpath] > 2:
                        logger.warning("write_file loop blocked: %s attempt %d", fpath, write_counts[fpath])
                        tool_output = (
                            f"[error] WRITE REJECTED. {fpath} already written {write_counts[fpath] - 1} times. "
                            "File content is correct from your earlier write. "
                            "Do NOT rewrite files. Call task_complete now with your summary and files_created list."
                        )
                        iterations.append(AgentIteration(
                            iteration=i + 1,
                            tool_name=name,
                            tool_input={"path": fpath, "content": "(blocked — duplicate write)"},
                            tool_output=tool_output,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        ))
                        results.append((call_id, tool_output))
                        continue

                tool_output = _execute_tool(sandbox, name, args, tool_server_map)

                iterations.append(AgentIteration(
                    iteration=i + 1,
                    tool_name=name,
                    tool_input=args,
                    tool_output=tool_output[:2000],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))

                results.append((call_id, tool_output[:4000]))

                if name == "task_complete":
                    final_output = args
                    task_completed = True
                    break

            provider.add_tool_results(results)

            if final_output:
                break

        # Forced synthesis safety net: the main loop can exit with an empty
        # summary in two cases — (a) the LLM returns no tool calls AND empty
        # text (break with text=""), (b) max_iterations is reached mid-
        # exploration. In both cases we've gathered real data via tools but
        # have no answer to show. Give the model one final chance to
        # synthesize, forbidden from calling tools.
        summary_text = final_output.get("summary", "") if isinstance(final_output, dict) else ""
        if not task_completed and not summary_text.strip() and iterations:
            logger.warning(
                "Agent produced no answer after %d tool calls — forcing synthesis",
                len(iterations),
            )
            provider.add_user_message(
                "Based on ALL tool results above, write your complete answer now. "
                "Do NOT call any more tools. If exploration was incomplete, state "
                "what you found and what remained unexplored. Produce a real answer "
                "even if partial — an empty response is never acceptable."
            )
            try:
                _, _, forced_text, tokens_in, tokens_out = await asyncio.to_thread(provider.call)
                total_in += tokens_in
                total_out += tokens_out
                if forced_text and forced_text.strip():
                    final_output = {"summary": forced_text, "synthesis_forced": True}
            except Exception as exc:
                logger.warning("Forced synthesis call failed: %s", exc)

        # Self-critique verification loop (DEC-069)
        verified = None
        verify_issues: list[str] = []
        if task_completed and ctx.verify_config and ctx.verify_config.enabled:
            try:
                from agentura_sdk.runner.verify import build_verify_prompt, parse_verify_response

                output_text = json.dumps(final_output, indent=2)
                verify_prompt = build_verify_prompt(ctx.verify_config.criteria, output_text)
                provider.add_user_message(verify_prompt)
                verify_response = provider.get_response()
                total_in += getattr(verify_response, "input_tokens", 0)
                total_out += getattr(verify_response, "output_tokens", 0)
                verify_text = provider.extract_text(verify_response)
                verified, verify_issues = parse_verify_response(verify_text)

                # If issues found and retries allowed, let agent self-correct
                if not verified and ctx.verify_config.max_retries > 0:
                    correction_prompt = (
                        f"The verification found issues:\n"
                        + "\n".join(f"- {i}" for i in verify_issues)
                        + "\n\nPlease fix these issues and call task_complete again."
                    )
                    provider.add_user_message(correction_prompt)
                    retry_response = provider.get_response()
                    total_in += getattr(retry_response, "input_tokens", 0)
                    total_out += getattr(retry_response, "output_tokens", 0)
                    retry_text = provider.extract_text(retry_response)
                    # Check if the retry resolved the issues
                    verified, verify_issues = parse_verify_response(retry_text) if "VERIFIED" in retry_text or "ISSUES" in retry_text else (True, [])

                    # If self-correction succeeded, auto-generate a reflexion
                    if verified:
                        try:
                            from agentura_sdk.memory import get_memory_store
                            store = get_memory_store()
                            skill_path = f"{ctx.domain}/{ctx.skill_name}"
                            store.add_reflexion(skill_path, {
                                "rule": f"Self-corrected: {verify_issues[0] if verify_issues else 'verification failure'}",
                                "applies_when": "similar output patterns",
                                "confidence": 0.6,
                                "source": "self-critique",
                            })
                        except Exception:
                            pass
            except Exception as exc:
                logger.debug("Self-critique verification failed: %s", exc)

        # Extract artifacts from sandbox before closing
        context_for_next: dict = {}
        files_created = final_output.get("files_created", [])
        if files_created:
            try:
                output_dir, artifacts = _extract_artifacts(sandbox, files_created, ctx.skill_name)
                context_for_next = {"artifacts_dir": output_dir, "artifacts": artifacts}
            except Exception as exc:
                logger.warning("artifact extraction failed: %s", exc)

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = (total_in * 3.0 + total_out * 15.0) / 1_000_000

        return SkillResult(
            skill_name=ctx.skill_name,
            success=task_completed or bool(iterations),
            output={
                **final_output,
                "iterations_count": len(iterations),
                "iterations": [it.model_dump() for it in iterations[-10:]],
            },
            reasoning_trace=[
                f"Agent loop: {len(iterations)} iterations",
                f"Sandbox template: {config.template}",
            ],
            model_used=model_id,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            context_for_next=context_for_next,
            verified=verified,
            verify_issues=verify_issues,
            injected_reflexion_ids=injected_reflexion_ids,
        )

    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={
                "error": str(e),
                "iterations_completed": len(iterations),
                "iterations": [it.model_dump() for it in iterations[-5:]],
            },
            model_used=model_id,
            latency_ms=latency_ms,
        )
    finally:
        sandbox_mod.close(sandbox)


async def execute_agent_streaming(
    ctx: SkillContext,
) -> AsyncGenerator[AgentIteration | SkillResult, None]:
    """Streaming variant — yields AgentIteration events, then the final SkillResult."""
    start = time.monotonic()
    config = ctx.sandbox_config or SandboxConfig()
    iterations: list[AgentIteration] = []

    # Build dynamic tool set (sandbox + MCP)
    all_tools, tool_server_map = _build_tool_set(ctx.mcp_bindings)
    if tool_server_map:
        logger.info("MCP tools loaded: %s", list(tool_server_map.keys()))

    # Compose prompt with memory recall and reflexions
    system_prompt, _reflexion_ids = _build_prompt_with_memory(ctx)

    try:
        provider = _get_provider(ctx.model, system_prompt, all_tools,
                                 max_tokens=config.max_tokens, budget_tokens=config.budget_tokens)
    except RuntimeError as e:
        yield SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e)},
        )
        return

    model_id = ctx.model
    sandbox = await sandbox_mod.create(config)

    try:
        provider.add_user_message(json.dumps(ctx.input_data, indent=2))
        final_output: dict = {}
        total_in = 0
        total_out = 0
        task_completed = False
        write_counts: dict[str, int] = {}  # track write_file calls per path

        for i in range(config.max_iterations):
            wants_tools, tool_calls, text, tokens_in, tokens_out = await asyncio.to_thread(provider.call)
            total_in += tokens_in
            total_out += tokens_out

            if not wants_tools:
                if not iterations:
                    logger.warning("Agent responded without tool use, nudging")
                    provider.add_user_message(
                        "You MUST use the available tools to complete this task. "
                        "Do not respond with text only. Start by calling the appropriate tool."
                    )
                    continue
                final_output = {"summary": text}
                break

            results: list[tuple[str, str]] = []
            for call_id, name, args in tool_calls:
                # Detect write_file loops — reject writes after 2 to same path
                if name == "write_file":
                    fpath = args.get("path", "")
                    write_counts[fpath] = write_counts.get(fpath, 0) + 1
                    if write_counts[fpath] > 2:
                        logger.warning("write_file loop blocked: %s attempt %d", fpath, write_counts[fpath])
                        tool_output = (
                            f"[error] WRITE REJECTED. {fpath} already written {write_counts[fpath] - 1} times. "
                            "File content is correct from your earlier write. "
                            "Do NOT rewrite files. Call task_complete now with your summary and files_created list."
                        )
                        iteration = AgentIteration(
                            iteration=i + 1,
                            tool_name=name,
                            tool_input={"path": fpath, "content": "(blocked — duplicate write)"},
                            tool_output=tool_output,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                        iterations.append(iteration)
                        yield iteration
                        results.append((call_id, tool_output))
                        continue

                tool_output = _execute_tool(sandbox, name, args, tool_server_map)

                iteration = AgentIteration(
                    iteration=i + 1,
                    tool_name=name,
                    tool_input=args,
                    tool_output=tool_output[:2000],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                iterations.append(iteration)
                yield iteration

                results.append((call_id, tool_output[:4000]))

                if name == "task_complete":
                    final_output = args
                    task_completed = True
                    break

            provider.add_tool_results(results)

            if final_output:
                break

        # Extract artifacts from sandbox before closing
        context_for_next: dict = {}
        files_created = final_output.get("files_created", [])
        if files_created:
            try:
                output_dir, artifacts = _extract_artifacts(sandbox, files_created, ctx.skill_name)
                context_for_next = {"artifacts_dir": output_dir, "artifacts": artifacts}
            except Exception as exc:
                logger.warning("artifact extraction failed: %s", exc)

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = (total_in * 3.0 + total_out * 15.0) / 1_000_000

        yield SkillResult(
            skill_name=ctx.skill_name,
            success=task_completed or bool(iterations),
            output={
                **final_output,
                "iterations_count": len(iterations),
            },
            reasoning_trace=[f"Agent loop: {len(iterations)} iterations"],
            model_used=model_id,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            context_for_next=context_for_next,
        )

    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        yield SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": str(e), "iterations_completed": len(iterations)},
            model_used=model_id,
            latency_ms=latency_ms,
        )
    finally:
        sandbox_mod.close(sandbox)
