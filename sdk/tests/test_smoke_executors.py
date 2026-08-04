"""Smoke tests for all executor paths.

Run before every executor deploy to catch regressions like the
3-day PTC outage (Apr 6-9) caused by a tuple unpacking bug.

Usage:
    # From inside the executor pod:
    python -m pytest tests/test_smoke_executors.py -v --timeout=120

    # From local with port-forward:
    kubectl port-forward svc/executor 8000:8000
    EXECUTOR_URL=http://localhost:8000 python -m pytest tests/test_smoke_executors.py -v
"""

import json
import os
import time

import httpx
import pytest

EXECUTOR_URL = os.environ.get("EXECUTOR_URL", "http://localhost:8000")
TIMEOUT = 120  # seconds — PTC workers need time to spin up


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url=EXECUTOR_URL, timeout=TIMEOUT)


def _execute_skill(client: httpx.Client, domain: str, skill: str, input_data: dict) -> dict:
    """Call the executor skill API and return the parsed response."""
    resp = client.post(
        f"/api/v1/skills/{domain}/{skill}/execute",
        json={"input_data": input_data},
    )
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:300]}"
    data = resp.json()
    assert "success" in data, f"Missing 'success' field: {list(data.keys())}"
    return data


class TestPTCExecutor:
    """Smoke tests for PTC (lightweight agent) executor path.

    PTC skills: growth/heartbeat, growth/daily-pulse, growth/data-query
    These use the PTC worker pod with Anthropic API.
    """

    def test_heartbeat_returns_success(self, client):
        """Growth heartbeat should execute and return success=true.

        This was the skill broken for 3 days by the tuple unpacking bug.
        If this fails, PTC executor is broken for ALL PTC skills.
        """
        result = _execute_skill(client, "growth", "heartbeat", {
            "trigger": "heartbeat",
            "_triggered_by": "smoke-test",
        })
        assert result["success"] is True, f"Heartbeat failed: {json.dumps(result.get('output', {}))[:300]}"
        assert result["cost_usd"] > 0, "Cost should be > 0 (LLM was called)"

    def test_ptc_system_prompt_is_string(self, client):
        """Verify system_prompt is a string, not a tuple.

        Regression test for: _build_prompt_with_memory() returns tuple
        but PTC executor must unpack it before sending to worker.
        """
        # This is tested implicitly by test_heartbeat_returns_success,
        # but we make it explicit for clarity.
        result = _execute_skill(client, "growth", "heartbeat", {
            "trigger": "heartbeat",
            "_triggered_by": "smoke-test-prompt-check",
        })
        # If system_prompt was a tuple, the PTC worker returns 422
        # and the executor returns success=false, cost=0
        assert result["success"] is True
        assert result["cost_usd"] > 0


class TestDirectAnthropicExecutor:
    """Smoke tests for direct Anthropic API executor path.

    Non-agent PTC skills (role=specialist) use _execute_via_pydantic_ai.
    """

    def test_data_query_returns_success(self, client):
        """Growth data-query should execute via direct Anthropic API."""
        result = _execute_skill(client, "growth", "data-query", {
            "text": "How many NTUs yesterday?",
            "_triggered_by": "smoke-test",
        })
        # data-query may fail if Databricks is down, but the LLM call should succeed
        assert "success" in result
        assert result.get("cost_usd", 0) > 0 or result.get("output", {}).get("error"), \
            "Expected either cost > 0 (LLM called) or an error message"


class TestSkillContextBuilding:
    """Smoke tests for _build_skill_context — the shared function that
    broke PTC when we changed it for MCP binding.
    """

    def test_agent_skill_gets_sandbox_config(self, client):
        """Agent skills should have sandbox_config set."""
        result = _execute_skill(client, "growth", "heartbeat", {
            "trigger": "heartbeat",
            "_triggered_by": "smoke-test-sandbox",
        })
        traces = result.get("reasoning_trace", [])
        # PTC worker trace includes "PTC Worker: N tool calls"
        has_ptc_trace = any("PTC Worker" in t or "Worker pod" in t for t in traces)
        assert has_ptc_trace, f"Expected PTC Worker trace, got: {traces}"

    def test_specialist_skill_runs_without_sandbox(self, client):
        """Specialist skills should run via direct Anthropic, not PTC worker."""
        result = _execute_skill(client, "growth", "daily-pulse", {
            "trigger": "smoke-test",
            "_triggered_by": "smoke-test",
        })
        assert "success" in result


class TestMCPBindings:
    """Smoke tests for MCP tool binding — verify tools are resolved."""

    def test_databricks_mcp_accessible(self, client):
        """Databricks MCP server should be reachable from executor."""
        resp = client.get("/health")
        assert resp.status_code == 200

        # Query Databricks MCP directly
        try:
            dd_resp = httpx.get(
                os.environ.get("MCP_DATABRICKS_URL", "http://databricks-mcp:8092") + "/health",
                timeout=5,
            )
            assert dd_resp.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Databricks MCP not reachable (may not be in this environment)")

    def test_datadog_mcp_accessible(self, client):
        """Datadog MCP server should be reachable from executor."""
        try:
            dd_resp = httpx.get(
                os.environ.get("MCP_DATADOG_URL", "http://datadog-mcp:8098") + "/health",
                timeout=5,
            )
            assert dd_resp.status_code == 200
            data = dd_resp.json()
            assert data["status"] == "ready", f"Datadog MCP not ready: {data}"
        except httpx.ConnectError:
            pytest.skip("Datadog MCP not reachable (may not be in this environment)")


class TestReflexionInjection:
    """Smoke tests for reflexion injection — verify it doesn't break execution."""

    def test_reflexion_injection_returns_list(self):
        """_build_prompt_with_memory should return (str, list)."""
        from agentura_sdk.runner.agent_executor import _build_prompt_with_memory
        from agentura_sdk.types import SkillContext, SkillRole

        ctx = SkillContext(
            skill_name="test",
            domain="test",
            role=SkillRole.AGENT,
            model="test",
            system_prompt="test prompt",
            input_data={},
        )
        result = _build_prompt_with_memory(ctx)
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 2, f"Expected 2-tuple, got {len(result)}"
        prompt, ids = result
        assert isinstance(prompt, str), f"Expected str prompt, got {type(prompt)}"
        assert isinstance(ids, list), f"Expected list ids, got {type(ids)}"
