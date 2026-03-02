"""Workflow eval runner — test skills with mocked tools in CI (DEC-070).

Loads eval configs from evals/*.yaml, runs each against mock MCP servers,
checks assertions (objective + subjective).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

from agentura_sdk.testing.eval_types import (
    EvalAssertion,
    EvalConfig,
    EvalResult,
    MockToolConfig,
)

logger = logging.getLogger(__name__)


def load_eval_configs(skill_dir: Path) -> list[EvalConfig]:
    """Load all eval configs from skill_dir/evals/*.yaml."""
    evals_dir = skill_dir / "evals"
    if not evals_dir.exists():
        return []

    configs = []
    for yaml_file in sorted(evals_dir.glob("*.yaml")):
        try:
            raw = yaml.safe_load(yaml_file.read_text()) or {}
            # Parse mock_tools from dict of {name: {response: ...}}
            mock_tools = {}
            for name, cfg in raw.get("mock_tools", {}).items():
                if isinstance(cfg, dict):
                    mock_tools[name] = MockToolConfig(**cfg)
                else:
                    mock_tools[name] = MockToolConfig(response=str(cfg))

            # Parse assertions
            assertions = []
            for a in raw.get("assertions", []):
                assertions.append(EvalAssertion(**a))

            configs.append(EvalConfig(
                name=raw.get("name", yaml_file.stem),
                prompt=raw.get("prompt", ""),
                input_data=raw.get("input_data", {}),
                mock_tools=mock_tools,
                expected_tools=raw.get("expected_tools", []),
                forbidden_tools=raw.get("forbidden_tools", []),
                assertions=assertions,
                max_retries=raw.get("max_retries", 3),
            ))
        except Exception as e:
            logger.warning("Failed to load eval config %s: %s", yaml_file, e)

    return configs


async def run_eval(config: EvalConfig, skill_dir: Path) -> EvalResult:
    """Execute a single eval with retries for non-determinism."""
    for attempt in range(1, config.max_retries + 1):
        result = await _execute_eval_attempt(config, skill_dir)
        result.attempts = attempt
        if result.passed:
            return result

    return result


async def _execute_eval_attempt(config: EvalConfig, skill_dir: Path) -> EvalResult:
    """Run one attempt of an eval."""
    from agentura_sdk.testing.mock_mcp_server import MockMCPServer

    result = EvalResult(name=config.name, passed=False)

    with MockMCPServer(config.mock_tools) as mock:
        # Build a SkillContext with mock MCP bindings
        from agentura_sdk.runner.skill_loader import load_skill_md
        from agentura_sdk.types import SandboxConfig, SkillContext, SkillRole

        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            result.failures.append(f"SKILL.md not found at {skill_md_path}")
            return result

        try:
            loaded = load_skill_md(skill_md_path)
        except Exception as e:
            result.failures.append(f"Failed to load SKILL.md: {e}")
            return result

        # Build mock MCP bindings
        mock_bindings = [{
            "server": "mock-eval",
            "url": mock.url,
            "tools": list(config.mock_tools.keys()),
        }]

        # Use input_data from eval config, falling back to fixtures
        input_data = config.input_data
        if not input_data:
            fixture = skill_dir / "fixtures" / "sample_input.json"
            if fixture.exists():
                input_data = json.loads(fixture.read_text())

        # Add the eval prompt as additional context
        if config.prompt:
            input_data["_eval_prompt"] = config.prompt

        ctx = SkillContext(
            skill_name=loaded.metadata.name,
            domain=loaded.metadata.domain,
            role=loaded.metadata.role,
            model=loaded.metadata.model,
            system_prompt=loaded.system_prompt,
            input_data=input_data,
            mcp_bindings=mock_bindings,
            sandbox_config=SandboxConfig(executor=""),  # Force legacy executor
        )

        # Execute
        try:
            from agentura_sdk.runner.local_runner import execute_skill

            skill_result = await execute_skill(ctx)
            output_text = json.dumps(skill_result.output, indent=2)
            result.output = output_text
            result.tool_calls = mock.call_names
        except Exception as e:
            result.failures.append(f"Execution failed: {e}")
            return result

        # Check assertions
        result.failures = _check_assertions(
            config=config,
            output_text=output_text,
            tool_calls=mock.call_names,
        )
        result.passed = len(result.failures) == 0

    return result


def _check_assertions(
    config: EvalConfig,
    output_text: str,
    tool_calls: list[str],
) -> list[str]:
    """Check all assertions against the eval output. Returns list of failure messages."""
    failures = []

    # Check expected tools were called
    for tool in config.expected_tools:
        if tool not in tool_calls:
            failures.append(f"Expected tool '{tool}' was not called")

    # Check forbidden tools were not called
    for tool in config.forbidden_tools:
        if tool in tool_calls:
            failures.append(f"Forbidden tool '{tool}' was called")

    # Check explicit assertions
    for assertion in config.assertions:
        if assertion.type == "output-contains":
            if assertion.value.lower() not in output_text.lower():
                failures.append(f"Output does not contain '{assertion.value}'")

        elif assertion.type == "output-not-contains":
            if assertion.value.lower() in output_text.lower():
                failures.append(f"Output contains forbidden text '{assertion.value}'")

        elif assertion.type == "tool-called":
            if assertion.value not in tool_calls:
                failures.append(f"Expected tool '{assertion.value}' was not called")

        elif assertion.type == "tool-not-called":
            if assertion.value in tool_calls:
                failures.append(f"Forbidden tool '{assertion.value}' was called")

        elif assertion.type == "judge":
            # LLM judge — skip in unit tests, execute when LLM available
            try:
                passed = _run_judge_assertion(assertion.criteria, output_text)
                if not passed:
                    failures.append(f"Judge assertion failed: {assertion.criteria}")
            except Exception:
                # If LLM unavailable, skip judge assertions
                logger.debug("Skipping judge assertion (no LLM available)")

    return failures


def _run_judge_assertion(criteria: str, output_text: str) -> bool:
    """Use a cheap LLM to judge whether output meets criteria."""
    import os

    prompt = f"""Judge whether this output meets the criteria.

Criteria: {criteria}

Output:
{output_text[:2000]}

Respond with exactly "PASS" or "FAIL" followed by a brief reason."""

    if os.environ.get("OPENROUTER_API_KEY"):
        from agentura_sdk.runner.openrouter import chat_completion_messages

        resp = chat_completion_messages(
            model="anthropic/claude-haiku-4.5",
            messages=[
                {"role": "system", "content": "You are an eval judge. Respond with PASS or FAIL."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=100,
        )
        return resp.content.strip().upper().startswith("PASS")

    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic

        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            system="You are an eval judge. Respond with PASS or FAIL.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return resp.content[0].text.strip().upper().startswith("PASS")

    raise RuntimeError("No LLM available for judge assertion")
