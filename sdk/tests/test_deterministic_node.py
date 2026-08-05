"""Tests for DeterministicNode in the pipeline engine."""

import asyncio
import os
import textwrap
from pathlib import Path

import pytest
import yaml

from agentura_sdk.pipelines.engine import (
    DeterministicNode,
    PipelineStep,
    _parse_steps,
    execute_deterministic_node,
    _run_flat_steps,
)


# ---------------------------------------------------------------------------
# YAML parsing
# ---------------------------------------------------------------------------


class TestParseSteps:
    """_parse_steps handles both skill and deterministic entries."""

    def test_parse_skill_only(self):
        raw = [{"skill": "dev/app-builder", "required": True}]
        steps = _parse_steps(raw)
        assert len(steps) == 1
        assert isinstance(steps[0], PipelineStep)
        assert steps[0].skill == "dev/app-builder"

    def test_parse_deterministic_only(self):
        raw = [
            {
                "deterministic": {
                    "id": "lint",
                    "command": "echo ok",
                    "timeout_seconds": 60,
                }
            }
        ]
        steps = _parse_steps(raw)
        assert len(steps) == 1
        assert isinstance(steps[0], DeterministicNode)
        assert steps[0].id == "lint"
        assert steps[0].command == "echo ok"
        assert steps[0].timeout_seconds == 60.0
        assert steps[0].always_runs is True

    def test_parse_mixed_steps(self):
        raw_yaml = textwrap.dedent("""\
            - skill: dev/app-builder
            - deterministic:
                id: lint
                command: "make lint"
                timeout_seconds: 60
            - deterministic:
                id: test
                command: "make test"
                timeout_seconds: 120
                always_runs: false
            - skill: dev/deployer
              required: false
        """)
        raw = yaml.safe_load(raw_yaml)
        steps = _parse_steps(raw)

        assert len(steps) == 4
        assert isinstance(steps[0], PipelineStep)
        assert steps[0].skill == "dev/app-builder"

        assert isinstance(steps[1], DeterministicNode)
        assert steps[1].id == "lint"
        assert steps[1].timeout_seconds == 60.0
        assert steps[1].always_runs is True

        assert isinstance(steps[2], DeterministicNode)
        assert steps[2].id == "test"
        assert steps[2].always_runs is False

        assert isinstance(steps[3], PipelineStep)
        assert steps[3].skill == "dev/deployer"
        assert steps[3].required is False

    def test_parse_deterministic_defaults(self):
        raw = [{"deterministic": {"id": "check", "command": "true"}}]
        steps = _parse_steps(raw)
        node = steps[0]
        assert isinstance(node, DeterministicNode)
        assert node.timeout_seconds == 30.0
        assert node.always_runs is True


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


class TestExecuteDeterministicNode:
    """execute_deterministic_node runs shell commands correctly."""

    @pytest.mark.asyncio
    async def test_successful_command(self, tmp_path):
        node = DeterministicNode(id="echo-test", command="echo hello")
        result = await execute_deterministic_node(node, {}, tmp_path)

        assert result["status"] == "ok"
        assert result["stdout"].strip() == "hello"
        assert result["stderr"] == ""
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_failing_command(self, tmp_path):
        node = DeterministicNode(id="fail-test", command="exit 1")
        result = await execute_deterministic_node(node, {}, tmp_path)

        assert result["status"] == "error"
        assert result["exit_code"] == 1

    @pytest.mark.asyncio
    async def test_timeout_enforcement(self, tmp_path):
        node = DeterministicNode(
            id="slow-test",
            command="sleep 10",
            timeout_seconds=0.5,
        )
        result = await execute_deterministic_node(node, {}, tmp_path)

        assert result["status"] == "timeout"
        assert result["exit_code"] == -1
        assert "timed out" in result["stderr"]

    @pytest.mark.asyncio
    async def test_env_vars_passed(self, tmp_path):
        node = DeterministicNode(
            id="env-test",
            command="echo $MY_VAR",
        )
        context = {"env": {"MY_VAR": "test-value-42"}}
        result = await execute_deterministic_node(node, context, tmp_path)

        assert result["status"] == "ok"
        assert result["stdout"].strip() == "test-value-42"

    @pytest.mark.asyncio
    async def test_cwd_is_run_root(self, tmp_path):
        node = DeterministicNode(id="cwd-test", command="pwd")
        result = await execute_deterministic_node(node, {}, tmp_path)

        assert result["status"] == "ok"
        # Resolve symlinks for macOS /private/tmp
        assert Path(result["stdout"].strip()).resolve() == tmp_path.resolve()

    @pytest.mark.asyncio
    async def test_stderr_captured(self, tmp_path):
        node = DeterministicNode(
            id="stderr-test",
            command="echo err >&2 && exit 0",
        )
        result = await execute_deterministic_node(node, {}, tmp_path)

        assert result["status"] == "ok"
        assert result["stderr"].strip() == "err"


# ---------------------------------------------------------------------------
# Integration with _run_flat_steps
# ---------------------------------------------------------------------------


class TestRunFlatStepsWithDeterministic:
    """DeterministicNode integrates into sequential step execution."""

    @pytest.mark.asyncio
    async def test_deterministic_node_in_flat_steps(self, tmp_path):
        """A successful deterministic node produces a result entry."""
        steps = [
            DeterministicNode(id="greet", command="echo hi"),
        ]
        results = await _run_flat_steps(steps, {}, {}, tmp_path)

        assert len(results) == 1
        r = results[0]
        assert r["type"] == "deterministic"
        assert r["node_id"] == "greet"
        assert r["status"] == "success"
        assert r["cost_usd"] == 0.0
        assert r["output"]["stdout"].strip() == "hi"

    @pytest.mark.asyncio
    async def test_always_runs_failure_stops_pipeline(self, tmp_path):
        """When always_runs=True and the node fails, subsequent steps are skipped."""
        steps = [
            DeterministicNode(id="must-pass", command="exit 1", always_runs=True),
            DeterministicNode(id="after", command="echo should-not-run"),
        ]
        results = await _run_flat_steps(steps, {}, {}, tmp_path)

        # Only the first step should have executed
        assert len(results) == 1
        assert results[0]["status"] == "error"

    @pytest.mark.asyncio
    async def test_always_runs_false_does_not_stop(self, tmp_path):
        """When always_runs=False and the node fails, subsequent steps still run."""
        steps = [
            DeterministicNode(id="optional", command="exit 1", always_runs=False),
            DeterministicNode(id="after", command="echo yes"),
        ]
        results = await _run_flat_steps(steps, {}, {}, tmp_path)

        assert len(results) == 2
        assert results[0]["status"] == "error"
        assert results[1]["status"] == "success"

    @pytest.mark.asyncio
    async def test_deterministic_output_in_carry_forward(self, tmp_path):
        """Deterministic node output is accessible via carry_forward."""
        steps = [
            DeterministicNode(id="producer", command="echo data123"),
        ]
        carry_forward: dict = {}
        await _run_flat_steps(steps, {}, carry_forward, tmp_path)

        key = "deterministic:producer"
        assert key in carry_forward
        assert carry_forward[key]["stdout"].strip() == "data123"
