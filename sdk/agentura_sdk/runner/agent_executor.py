"""Multi-turn agent executor with provider abstraction.

Supports OpenRouter (primary) and Anthropic SDK (fallback) for tool calling.
Provider selected via env vars: OPENROUTER_API_KEY first, ANTHROPIC_API_KEY second.
Sandbox backend selected via SANDBOX_BACKEND env var (docker | k8s).
"""

from __future__ import annotations

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

# OpenAI-format tools (used by OpenRouter)
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
        },
    }
    for t in SANDBOX_TOOLS
]


# --- Provider abstraction ---
# Normalized call result: (wants_tool_use, tool_calls[(id, name, args)], text, tokens_in, tokens_out)
_CallResult = tuple[bool, list[tuple[str, str, dict]], str, int, int]


class _OpenRouterProvider:
    """OpenAI-compatible tool calling via OpenRouter."""

    def __init__(self, model_id: str, system_prompt: str):
        from agentura_sdk.runner.openrouter import resolve_model
        self._model = resolve_model(model_id)
        self._messages: list[dict] = [{"role": "system", "content": system_prompt}]

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def call(self) -> _CallResult:
        from agentura_sdk.runner.openrouter import tool_chat_completion
        resp = tool_chat_completion(self._model, self._messages, OPENAI_TOOLS)

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

    def __init__(self, model_id: str, system_prompt: str, api_key: str):
        from anthropic import Anthropic
        self._client = Anthropic(api_key=api_key)
        self._model = model_id
        self._system = system_prompt
        self._messages: list[dict] = []

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def call(self) -> _CallResult:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=self._system,
            tools=SANDBOX_TOOLS,
            messages=self._messages,
        )

        assistant_content = response.content
        self._messages.append({"role": "assistant", "content": assistant_content})

        wants_tools = response.stop_reason == "tool_use"
        text_parts = [b.text for b in assistant_content if b.type == "text"]
        calls = [(b.id, b.name, b.input) for b in assistant_content if b.type == "tool_use"]

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
        "claude-sonnet-4.5": "claude-sonnet-4-5-latest",
        "claude-haiku-4.5": "claude-haiku-4-5-latest",
    }
    return aliases.get(name, name)


def _get_provider(model: str, system_prompt: str) -> _OpenRouterProvider | _AnthropicProvider:
    """Select provider: OpenRouter primary, Anthropic fallback."""
    if os.environ.get("OPENROUTER_API_KEY"):
        logger.info("Using OpenRouter provider for agent execution")
        return _OpenRouterProvider(model, system_prompt)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        logger.info("Using Anthropic provider for agent execution")
        model_id = _resolve_anthropic_model(model)
        return _AnthropicProvider(model_id, system_prompt, api_key)

    raise RuntimeError(
        "No LLM provider configured. Set OPENROUTER_API_KEY (preferred) or ANTHROPIC_API_KEY."
    )


# --- Tool execution ---

def _execute_tool(sandbox: object, tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call to the sandbox backend."""
    if tool_name == "write_file":
        return sandbox_mod.write_file(sandbox, tool_input["path"], tool_input["content"])
    if tool_name == "read_file":
        return sandbox_mod.read_file(sandbox, tool_input["path"])
    if tool_name == "run_command":
        return sandbox_mod.run_command(sandbox, tool_input["command"])
    if tool_name == "run_code":
        return sandbox_mod.run_code(sandbox, tool_input["code"])
    if tool_name == "clone_repo":
        return _clone_repo(sandbox, tool_input)
    if tool_name == "create_branch":
        return _create_branch(sandbox, tool_input)
    if tool_name == "create_pr":
        return _create_pr(sandbox, tool_input)
    if tool_name == "task_complete":
        return json.dumps(tool_input)
    return f"Unknown tool: {tool_name}"


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


# --- Agent loops ---

async def execute_agent(ctx: SkillContext) -> SkillResult:
    """Run the multi-turn agent loop: LLM tool calling → sandbox → iterate."""
    start = time.monotonic()
    config = ctx.sandbox_config or SandboxConfig()
    iterations: list[AgentIteration] = []

    try:
        provider = _get_provider(ctx.model, ctx.system_prompt)
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

        for i in range(config.max_iterations):
            wants_tools, tool_calls, text, tokens_in, tokens_out = provider.call()
            total_in += tokens_in
            total_out += tokens_out

            if not wants_tools:
                final_output = {"summary": text}
                break

            results: list[tuple[str, str]] = []
            for call_id, name, args in tool_calls:
                tool_output = _execute_tool(sandbox, name, args)

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

        return SkillResult(
            skill_name=ctx.skill_name,
            success=True,
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

    try:
        provider = _get_provider(ctx.model, ctx.system_prompt)
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

        for i in range(config.max_iterations):
            wants_tools, tool_calls, text, tokens_in, tokens_out = provider.call()
            total_in += tokens_in
            total_out += tokens_out

            if not wants_tools:
                final_output = {"summary": text}
                break

            results: list[tuple[str, str]] = []
            for call_id, name, args in tool_calls:
                tool_output = _execute_tool(sandbox, name, args)

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
            success=True,
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
