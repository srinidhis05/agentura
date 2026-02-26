"""Multi-turn agent executor: Claude tool_use → E2B sandbox → iterate.

Uses the Anthropic SDK directly (not Pydantic AI) for raw tool_use control.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from anthropic import Anthropic

from agentura_sdk.sandbox import e2b_sandbox
from agentura_sdk.types import AgentIteration, SandboxConfig, SkillContext, SkillResult

# Tool definitions exposed to Claude
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


def _execute_tool(sandbox: object, tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call to the E2B sandbox."""
    if tool_name == "write_file":
        return e2b_sandbox.write_file(sandbox, tool_input["path"], tool_input["content"])
    if tool_name == "read_file":
        return e2b_sandbox.read_file(sandbox, tool_input["path"])
    if tool_name == "run_command":
        return e2b_sandbox.run_command(sandbox, tool_input["command"])
    if tool_name == "run_code":
        return e2b_sandbox.run_code(sandbox, tool_input["code"])
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
    return e2b_sandbox.run_command(sandbox, cmd)


def _create_branch(sandbox: object, params: dict) -> str:
    branch = params["branch_name"]
    base_dir = params.get("base_dir", "/home/user/repo")
    cmd = f"cd {base_dir} && git checkout -b {branch}"
    return e2b_sandbox.run_command(sandbox, cmd)


def _create_pr(sandbox: object, params: dict) -> str:
    title = params["title"].replace('"', '\\"')
    body = params["body"].replace('"', '\\"')
    base_dir = params.get("base_dir", "/home/user/repo")
    cmd = (
        f'cd {base_dir} && git add -A && git commit -m "{title}" '
        f'&& git push -u origin HEAD '
        f'&& gh pr create --title "{title}" --body "{body}"'
    )
    return e2b_sandbox.run_command(sandbox, cmd)


def _resolve_model(model: str) -> str:
    """Resolve model string to Anthropic model ID."""
    name = model.removeprefix("anthropic/")
    aliases = {
        "claude-sonnet-4.5": "claude-sonnet-4-5-latest",
        "claude-haiku-4.5": "claude-haiku-4-5-latest",
    }
    return aliases.get(name, name)


async def execute_agent(ctx: SkillContext) -> SkillResult:
    """Run the multi-turn agent loop: Claude tool_use → E2B sandbox → iterate."""
    start = time.monotonic()
    config = ctx.sandbox_config or SandboxConfig()
    iterations: list[AgentIteration] = []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "ANTHROPIC_API_KEY required for agent execution"},
        )

    client = Anthropic(api_key=api_key)
    model_id = _resolve_model(ctx.model)

    # Create sandbox
    sandbox = await e2b_sandbox.create(config)

    try:
        messages: list[dict] = [
            {"role": "user", "content": json.dumps(ctx.input_data, indent=2)},
        ]

        final_output: dict = {}

        for i in range(config.max_iterations):
            response = client.messages.create(
                model=model_id,
                max_tokens=4096,
                system=ctx.system_prompt,
                tools=SANDBOX_TOOLS,
                messages=messages,
            )

            # Collect assistant content blocks
            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            # Check if the model wants to use tools
            if response.stop_reason != "tool_use":
                # Model finished without tool calls — extract text
                text_parts = [b.text for b in assistant_content if b.type == "text"]
                final_output = {"summary": "\n".join(text_parts)}
                break

            # Process each tool_use block
            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input = block.input

                # Execute in sandbox
                tool_output = _execute_tool(sandbox, tool_name, tool_input)

                iterations.append(AgentIteration(
                    iteration=i + 1,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_output=tool_output[:2000],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tool_output[:4000],
                })

                # If task_complete, capture final output
                if tool_name == "task_complete":
                    final_output = tool_input
                    break

            messages.append({"role": "user", "content": tool_results})

            if final_output:
                break

        latency_ms = (time.monotonic() - start) * 1000

        # Estimate cost from usage
        cost_usd = 0.0
        if hasattr(response, "usage"):
            input_tokens = getattr(response.usage, "input_tokens", 0)
            output_tokens = getattr(response.usage, "output_tokens", 0)
            # Approximate cost (Sonnet 4.5 pricing)
            cost_usd = (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000

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
        e2b_sandbox.close(sandbox)


async def execute_agent_streaming(
    ctx: SkillContext,
) -> AsyncGenerator[AgentIteration | SkillResult, None]:
    """Streaming variant — yields AgentIteration events, then the final SkillResult."""
    start = time.monotonic()
    config = ctx.sandbox_config or SandboxConfig()
    iterations: list[AgentIteration] = []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        yield SkillResult(
            skill_name=ctx.skill_name,
            success=False,
            output={"error": "ANTHROPIC_API_KEY required for agent execution"},
        )
        return

    client = Anthropic(api_key=api_key)
    model_id = _resolve_model(ctx.model)
    sandbox = await e2b_sandbox.create(config)

    try:
        messages: list[dict] = [
            {"role": "user", "content": json.dumps(ctx.input_data, indent=2)},
        ]
        final_output: dict = {}
        response = None

        for i in range(config.max_iterations):
            response = client.messages.create(
                model=model_id,
                max_tokens=4096,
                system=ctx.system_prompt,
                tools=SANDBOX_TOOLS,
                messages=messages,
            )

            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            if response.stop_reason != "tool_use":
                text_parts = [b.text for b in assistant_content if b.type == "text"]
                final_output = {"summary": "\n".join(text_parts)}
                break

            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use":
                    continue

                tool_output = _execute_tool(sandbox, block.name, block.input)

                iteration = AgentIteration(
                    iteration=i + 1,
                    tool_name=block.name,
                    tool_input=block.input,
                    tool_output=tool_output[:2000],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                iterations.append(iteration)
                yield iteration

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tool_output[:4000],
                })

                if block.name == "task_complete":
                    final_output = block.input
                    break

            messages.append({"role": "user", "content": tool_results})

            if final_output:
                break

        latency_ms = (time.monotonic() - start) * 1000
        cost_usd = 0.0
        if response and hasattr(response, "usage"):
            input_tokens = getattr(response.usage, "input_tokens", 0)
            output_tokens = getattr(response.usage, "output_tokens", 0)
            cost_usd = (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000

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
        e2b_sandbox.close(sandbox)
