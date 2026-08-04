"""Claude Code Worker — isolated FastAPI server wrapping claude-agent-sdk.

Each worker pod handles a single agent execution, streaming SSE events
back to the executor. Created/destroyed per-request by claude_code_worker.py.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

WORK_DIR = os.environ.get("WORK_DIR", "/home/worker/workspace")
MAX_CONTINUATIONS = int(os.environ.get("MAX_CONTINUATIONS", "2"))

app = FastAPI(title="Claude Code Worker", version="0.1.0")

# Configure root logger so logger.info() actually outputs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _setup_git_credentials(request: AgentRequest) -> None:
    """Configure git to authenticate with GitHub using the available token.

    Priority: GITHUB_TOKEN env var > github_token from input data > skip.
    Sets up a global git credential helper so `git clone https://github.com/...`
    works without the agent needing to manually configure auth.
    """
    import subprocess

    # Try env var first (from K8s secret), then input data
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            input_data = json.loads(request.prompt)
            token = input_data.get("github_token", "")
        except (json.JSONDecodeError, AttributeError):
            pass

    if not token:
        logger.info("No GitHub token available — git clone will require manual auth")
        return

    # Configure git to use token for all github.com HTTPS URLs
    subprocess.run(
        ["git", "config", "--global", "url.https://x-access-token:" + token + "@github.com/.insteadOf", "https://github.com/"],
        capture_output=True,
    )
    # Also configure gh CLI
    subprocess.run(
        ["gh", "auth", "setup-git"],
        capture_output=True,
        env={**os.environ, "GITHUB_TOKEN": token, "GH_TOKEN": token},
    )
    logger.info("Git credentials configured for github.com")


def _write_claude_md(request: AgentRequest) -> None:
    """Write CLAUDE.md to workspace — strongest behavioral signal for Claude Code.

    Claude Code reads CLAUDE.md as project-level instructions that take priority
    over its default "software engineering assistant" behavior.
    """
    claude_md_path = Path(WORK_DIR) / "CLAUDE.md"

    if request.task_type == "review":
        claude_md = (
            "# CLAUDE.md — Agentura Review Agent\n\n"
            "You are executing a CODE REVIEW task inside an Agentura worker pod.\n\n"
            "## CRITICAL RULES\n\n"
            "1. **READ-ONLY** — Do NOT create files, write code, commit, push, or create PRs.\n"
            "   The ONLY file you may write is `TASK_RESULT.json`.\n"
            "2. **Output format** — You MUST write your findings to `TASK_RESULT.json` as valid JSON.\n"
            "   The JSON schema is defined in your system prompt. Follow it exactly.\n"
            "3. **No exploration loops** — Do not broadly explore the codebase. The PR diff and\n"
            "   changed files are provided in your input. Analyze THOSE, not the whole repo.\n"
            "4. **Evidence required** — Every finding must cite file:line and include a code snippet.\n"
            "5. **Finish with TASK_RESULT.json** — Your task is NOT complete until this file exists.\n"
            "   Write it using the Write tool as the LAST thing you do.\n\n"
            "## What NOT to do\n\n"
            "- Do NOT run `git push`, `git commit`, or `gh pr create`\n"
            "- Do NOT create branches or modify the git state\n"
            "- Do NOT produce a text-only summary without writing TASK_RESULT.json\n"
            "- Do NOT ask follow-up questions — produce the verdict and stop\n"
        )
    else:
        claude_md = (
            "# CLAUDE.md — Agentura Build Agent\n\n"
            "You are executing a BUILD task inside an Agentura worker pod.\n\n"
            "## CRITICAL RULES\n\n"
            "1. **Follow the system prompt** — Your task instructions are in the system prompt.\n"
            "2. **Output format** — When done, write `TASK_RESULT.json` with your results.\n"
            "3. **Stay focused** — Complete the task described. Do not explore unrelated code.\n"
            "4. **Finish with TASK_RESULT.json** — Your task is NOT complete until this file exists.\n"
        )

    claude_md_path.write_text(claude_md)
    logger.info("Wrote CLAUDE.md for task_type=%s", request.task_type)


def _build_continuation(
    task_type: str, summary: str, original_prompt: str, work_dir: str,
) -> tuple[str, str]:
    """Build task-type-aware continuation system prompt and user prompt."""

    if task_type == "review":
        cont_system = (
            "You are a review delivery agent. A previous agent analyzed code but stopped "
            "before writing TASK_RESULT.json. Your ONLY job is to:\n"
            "1. Read the previous agent's analysis from the conversation\n"
            "2. Synthesize it into the required JSON schema\n"
            "3. Write TASK_RESULT.json to " + work_dir + "\n\n"
            "Do NOT explore the codebase. Do NOT create PRs. Do NOT commit code.\n"
            "ONLY write TASK_RESULT.json based on what the previous agent found."
        )
        continuation_prompt = (
            "A previous review agent analyzed code but stopped before writing TASK_RESULT.json.\n\n"
            "Previous agent findings:\n" + summary[:3000] + "\n\n"
            "Original task:\n" + original_prompt[:2000] + "\n\n"
            "Write " + work_dir + "/TASK_RESULT.json with the review findings in the JSON "
            "schema defined in the system prompt. If the previous agent didn't produce a clear "
            "verdict, use verdict: 'CONDITIONAL' and list what needs manual review under conditions.\n"
            "IMPORTANT: Use the Write tool to create TASK_RESULT.json. Do nothing else."
        )
    else:
        cont_system = (
            "You are a delivery agent. A previous agent created code in a git repo "
            "but stopped before pushing and creating a PR. Your ONLY job is to:\n"
            "1. Find the git repo in /tmp/\n"
            "2. Commit all changes, push the branch\n"
            "3. Create a PR\n"
            "4. If an APK exists under build/, upload it via gh release create\n"
            "5. Write TASK_RESULT.json with pr_url and apk_url\n\n"
            "Do NOT create new code. Do NOT re-clone. Do NOT read documentation. "
            "Just push what exists and create the PR.\n"
            "NEVER produce a text-only response without tool calls."
        )
        continuation_prompt = (
            "A previous agent was working on this task but stopped before delivery.\n\n"
            "Previous agent summary:\n" + summary[:2000] + "\n\n"
            "Original task input:\n" + original_prompt[:2000] + "\n\n"
            "Steps — execute ALL with tool calls:\n"
            "1. Run: find /tmp -maxdepth 2 -name '.git' -type d\n"
            "2. cd into the repo directory found above\n"
            "3. Run: git status (see what files were created)\n"
            "4. Run: git add -A && git commit -m 'feat: add feature from incubation spec'\n"
            "5. Run: git push --force-with-lease origin HEAD\n"
            "6. Run: gh pr create --base <target> --title 'feat: add feature' "
            "--body 'Generated by Agentura incubator pipeline.'\n"
            "   (use the target branch specified in the skill config)\n"
            "7. If APK exists: find . -name '*.apk' -path '*/debug/*'\n"
            "   If found, run: gh release create incubator-$(date +%s) <apk_path> "
            "--repo <repo> --title 'Incubator debug APK' --prerelease\n"
            "8. Write " + work_dir + "/TASK_RESULT.json:\n"
            '   {"success": true, "pr_url": "<url from step 6>", '
            '"apk_url": "<release url from step 7 or null>", '
            '"summary": "Created feature. PR: <url>"}\n'
        )

    return cont_system, continuation_prompt


class AgentRequest(BaseModel):
    prompt: str
    system_prompt: str
    model: str = "claude-sonnet-4-5-20250929"
    max_turns: int = 25
    max_budget_usd: float | None = None
    mcp_servers: dict = Field(default_factory=dict)
    allowed_tools: list[str] = Field(default_factory=list)
    verify_criteria: list[str] = Field(default_factory=list)
    verify_max_retries: int = 1
    task_type: str = "build"  # "build" | "review" — controls continuation behavior


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/execute-stream")
async def execute_stream(request: AgentRequest):
    """Run Claude Code agent and stream SSE events."""
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
        UserMessage,
        query,
    )

    async def event_generator():
        start = time.monotonic()
        iteration_count = 0

        # Write input to workspace — git init required by Claude Code SDK
        import subprocess
        Path(WORK_DIR).mkdir(parents=True, exist_ok=True)
        if not (Path(WORK_DIR) / ".git").exists():
            subprocess.run(["git", "init"], cwd=WORK_DIR, capture_output=True)
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "init"],
                cwd=WORK_DIR, capture_output=True,
                env={**os.environ, "GIT_AUTHOR_NAME": "agentura", "GIT_AUTHOR_EMAIL": "bot@agentura",
                     "GIT_COMMITTER_NAME": "agentura", "GIT_COMMITTER_EMAIL": "bot@agentura"},
            )

        # Configure git credentials so the agent can clone repos.
        # Uses GITHUB_TOKEN from env (set via K8s secret) or github_token from input.
        _setup_git_credentials(request)

        # Write CLAUDE.md — strongest signal to Claude Code about behavior.
        # This overrides CC's default "software engineering assistant" persona.
        _write_claude_md(request)

        allowed_tools = request.allowed_tools or [
            "Read", "Write", "Edit", "Bash", "Glob", "Grep",
        ]

        options = ClaudeAgentOptions(
            system_prompt=request.system_prompt,
            allowed_tools=allowed_tools,
            mcp_servers=request.mcp_servers or {},
            permission_mode="bypassPermissions",
            cwd=WORK_DIR,
            max_turns=request.max_turns,
            max_budget_usd=request.max_budget_usd,
            model=request.model,
        )

        result_msg = None
        total_cost = 0.0
        final_text_parts: list[str] = []

        async def run_query(prompt: str, opts: ClaudeAgentOptions):
            """Run a query and stream events, returning the ResultMessage."""
            nonlocal iteration_count, result_msg, total_cost
            async for message in query(prompt=prompt, options=opts):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            iteration_count += 1
                            # Log every tool call for debugging
                            input_preview = str(block.input)[:200] if block.input else ""
                            logger.info(
                                "iter=%d tool=%s input=%s",
                                iteration_count, block.name, input_preview,
                            )
                            yield _sse("iteration", {
                                "iteration": iteration_count,
                                "tool_name": block.name,
                                "tool_input": block.input,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                        elif isinstance(block, TextBlock):
                            final_text_parts.append(block.text)
                            logger.info("agent_text: %s", block.text[:300])

                elif isinstance(message, UserMessage):
                    if isinstance(message.content, list):
                        for block in message.content:
                            if isinstance(block, ToolResultBlock) and block.tool_use_id:
                                content = block.content
                                output = ""
                                if isinstance(content, str):
                                    output = content[:2000]
                                elif isinstance(content, list):
                                    text_parts = [
                                        c.get("text", "") for c in content
                                        if isinstance(c, dict) and c.get("type") == "text"
                                    ]
                                    output = "\n".join(text_parts)[:2000]
                                yield _sse("tool_result", {
                                    "tool_use_id": block.tool_use_id,
                                    "output": output,
                                })

                elif isinstance(message, ResultMessage):
                    result_msg = message
                    if message.total_cost_usd:
                        total_cost += message.total_cost_usd

        try:
            # Main execution
            async for event in run_query(request.prompt, options):
                yield event

            # Continuation loop: if TASK_RESULT.json not written, retry
            result_path = Path(WORK_DIR) / "TASK_RESULT.json"
            logger.info(
                "main execution done. iterations=%d, TASK_RESULT exists=%s, task_type=%s",
                iteration_count, result_path.exists(), request.task_type,
            )
            continuation = 0
            while not result_path.exists() and continuation < MAX_CONTINUATIONS:
                continuation += 1
                remaining_turns = max(request.max_turns - iteration_count, 10)
                logger.info(
                    "TASK_RESULT.json missing after %d iterations, "
                    "continuation %d/%d with %d turns",
                    iteration_count, continuation, MAX_CONTINUATIONS, remaining_turns,
                )
                yield _sse("continuation", {
                    "attempt": continuation,
                    "reason": "TASK_RESULT.json not found",
                    "iterations_so_far": iteration_count,
                })

                # Summarize what was done so the continuation has context
                summary = "\n".join(final_text_parts[-3:]) if final_text_parts else ""

                cont_system, continuation_prompt = _build_continuation(
                    request.task_type, summary, request.prompt, WORK_DIR,
                )

                cont_options = ClaudeAgentOptions(
                    system_prompt=cont_system,
                    allowed_tools=allowed_tools,
                    mcp_servers=request.mcp_servers or {},
                    permission_mode="bypassPermissions",
                    cwd=WORK_DIR,
                    max_turns=min(remaining_turns, 15),
                    max_budget_usd=1.0,
                    model=request.model,
                )

                async for event in run_query(continuation_prompt, cont_options):
                    yield event

            # Read TASK_RESULT.json if exists
            task_result = {}
            result_path = Path(WORK_DIR) / "TASK_RESULT.json"
            if result_path.exists():
                try:
                    task_result = json.loads(result_path.read_text())
                except (json.JSONDecodeError, OSError):
                    pass

            # Collect artifacts from workspace
            artifacts: dict[str, str] = {}
            work_path = Path(WORK_DIR)
            for fpath in work_path.rglob("*"):
                if fpath.is_file() and fpath.name not in ("INPUT.json", "TASK_RESULT.json"):
                    rel = str(fpath.relative_to(work_path))
                    try:
                        artifacts[rel] = fpath.read_text()
                    except (UnicodeDecodeError, OSError):
                        artifacts[rel] = f"<binary: {fpath.stat().st_size} bytes>"

            # Self-critique verification (DEC-069)
            verified = None
            verify_issues: list[str] = []
            if not (result_msg and result_msg.is_error) and request.verify_criteria:
                try:
                    yield _sse("verify_start", {"criteria": request.verify_criteria})

                    output_text = json.dumps(task_result, indent=2) if task_result else "\n".join(final_text_parts)
                    criteria_block = "\n".join(f"- {c}" for c in request.verify_criteria)
                    verify_prompt = (
                        f"Verify the output against these criteria:\n{criteria_block}\n\n"
                        f"Output:\n{output_text[:4000]}\n\n"
                        f"Respond with VERIFIED: or ISSUES:"
                    )
                    # Use read-only tools for verification
                    verify_options = ClaudeAgentOptions(
                        system_prompt="You are verifying agent output. Only use Read and Bash (read-only) tools.",
                        allowed_tools=["Read", "Bash"],
                        permission_mode="bypassPermissions",
                        cwd=WORK_DIR,
                        max_turns=1,
                        model=request.model,
                    )
                    async for msg in query(prompt=verify_prompt, options=verify_options):
                        if isinstance(msg, ResultMessage):
                            pass
                        elif isinstance(msg, AssistantMessage):
                            for block in msg.content:
                                if isinstance(block, TextBlock):
                                    vtext = block.text.strip()
                                    if vtext.upper().startswith("VERIFIED"):
                                        verified = True
                                        yield _sse("verify_pass", {"message": vtext})
                                    else:
                                        verified = False
                                        verify_issues = [vtext[:500]]
                                        yield _sse("verify_fail", {"issues": verify_issues})
                except Exception as vexc:
                    logger.debug("Verification failed: %s", vexc)

            latency_ms = (time.monotonic() - start) * 1000
            cost_usd = total_cost
            session_id = result_msg.session_id if result_msg else ""
            is_error = result_msg.is_error if result_msg else False

            yield _sse("result", {
                "success": not is_error,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "session_id": session_id,
                "iterations_count": iteration_count,
                "task_result": task_result,
                "summary": "\n".join(final_text_parts),
                "artifacts": artifacts,
                "verified": verified,
                "verify_issues": verify_issues,
            })

        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            logger.error("Agent execution failed: %s", exc)
            yield _sse("error", {
                "error": str(exc),
                "latency_ms": latency_ms,
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
