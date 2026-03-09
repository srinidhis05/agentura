"""Tests for workflow eval runner (DEC-070)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from agentura_sdk.testing.eval_types import EvalAssertion, EvalConfig, MockToolConfig, EvalResult
from agentura_sdk.testing.eval_runner import load_eval_configs, _check_assertions


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    """Create a minimal skill directory with evals."""
    skill = tmp_path / "dev" / "deployer"
    skill.mkdir(parents=True)

    # SKILL.md
    (skill / "SKILL.md").write_text(
        "---\nname: deployer\nrole: agent\ndomain: dev\n---\nDeploy things."
    )

    # evals directory
    evals = skill / "evals"
    evals.mkdir()

    return skill


class TestLoadEvalConfigs:
    def test_loads_valid_yaml(self, skill_dir: Path):
        eval_yaml = {
            "name": "test-deploy",
            "prompt": "Deploy it",
            "mock_tools": {"kubectl_apply": {"response": "created"}},
            "expected_tools": ["kubectl_apply"],
            "assertions": [{"type": "output-contains", "value": "deployed"}],
        }
        (skill_dir / "evals" / "test-deploy.yaml").write_text(yaml.dump(eval_yaml))

        configs = load_eval_configs(skill_dir)
        assert len(configs) == 1
        assert configs[0].name == "test-deploy"
        assert configs[0].prompt == "Deploy it"
        assert "kubectl_apply" in configs[0].mock_tools
        assert configs[0].expected_tools == ["kubectl_apply"]

    def test_loads_multiple_configs_sorted(self, skill_dir: Path):
        for name in ["b-eval", "a-eval"]:
            (skill_dir / "evals" / f"{name}.yaml").write_text(
                yaml.dump({"name": name, "prompt": f"Test {name}"})
            )
        configs = load_eval_configs(skill_dir)
        assert len(configs) == 2
        assert configs[0].name == "a-eval"
        assert configs[1].name == "b-eval"

    def test_empty_evals_dir(self, skill_dir: Path):
        configs = load_eval_configs(skill_dir)
        assert configs == []

    def test_no_evals_dir(self, tmp_path: Path):
        configs = load_eval_configs(tmp_path / "nonexistent")
        assert configs == []

    def test_invalid_yaml_skipped(self, skill_dir: Path):
        (skill_dir / "evals" / "bad.yaml").write_text(": invalid: yaml: [")
        (skill_dir / "evals" / "good.yaml").write_text(
            yaml.dump({"name": "good", "prompt": "Test"})
        )
        configs = load_eval_configs(skill_dir)
        # Good config loaded, bad one skipped
        assert len(configs) >= 1
        assert any(c.name == "good" for c in configs)

    def test_mock_tool_string_response(self, skill_dir: Path):
        eval_yaml = {
            "name": "simple",
            "prompt": "Test",
            "mock_tools": {"my_tool": {"response": "ok"}},
        }
        (skill_dir / "evals" / "simple.yaml").write_text(yaml.dump(eval_yaml))
        configs = load_eval_configs(skill_dir)
        assert configs[0].mock_tools["my_tool"].response == "ok"

    def test_defaults_name_from_filename(self, skill_dir: Path):
        (skill_dir / "evals" / "my-eval.yaml").write_text(
            yaml.dump({"prompt": "Test without name"})
        )
        configs = load_eval_configs(skill_dir)
        assert configs[0].name == "my-eval"


class TestCheckAssertions:
    def test_expected_tool_called(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            expected_tools=["kubectl_apply"],
        )
        failures = _check_assertions(
            config=config,
            output_text="deployed",
            tool_calls=["kubectl_apply", "kubectl_get"],
        )
        assert failures == []

    def test_expected_tool_not_called(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            expected_tools=["kubectl_apply"],
        )
        failures = _check_assertions(
            config=config,
            output_text="output",
            tool_calls=["kubectl_get"],
        )
        assert len(failures) == 1
        assert "kubectl_apply" in failures[0]

    def test_forbidden_tool_called(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            forbidden_tools=["kubectl_delete"],
        )
        failures = _check_assertions(
            config=config,
            output_text="output",
            tool_calls=["kubectl_apply", "kubectl_delete"],
        )
        assert len(failures) == 1
        assert "kubectl_delete" in failures[0]

    def test_forbidden_tool_not_called(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            forbidden_tools=["kubectl_delete"],
        )
        failures = _check_assertions(
            config=config,
            output_text="output",
            tool_calls=["kubectl_apply"],
        )
        assert failures == []

    def test_output_contains_assertion_pass(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            assertions=[EvalAssertion(type="output-contains", value="deployed")],
        )
        failures = _check_assertions(
            config=config,
            output_text='{"status": "deployed successfully"}',
            tool_calls=[],
        )
        assert failures == []

    def test_output_contains_assertion_fail(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            assertions=[EvalAssertion(type="output-contains", value="deployed")],
        )
        failures = _check_assertions(
            config=config,
            output_text='{"status": "error"}',
            tool_calls=[],
        )
        assert len(failures) == 1
        assert "deployed" in failures[0]

    def test_output_contains_case_insensitive(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            assertions=[EvalAssertion(type="output-contains", value="DEPLOYED")],
        )
        failures = _check_assertions(
            config=config,
            output_text="Successfully deployed",
            tool_calls=[],
        )
        assert failures == []

    def test_output_not_contains_assertion_pass(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            assertions=[EvalAssertion(type="output-not-contains", value="error")],
        )
        failures = _check_assertions(
            config=config,
            output_text="Success",
            tool_calls=[],
        )
        assert failures == []

    def test_output_not_contains_assertion_fail(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            assertions=[EvalAssertion(type="output-not-contains", value="error")],
        )
        failures = _check_assertions(
            config=config,
            output_text="An error occurred",
            tool_calls=[],
        )
        assert len(failures) == 1

    def test_tool_called_assertion(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            assertions=[EvalAssertion(type="tool-called", value="kubectl_apply")],
        )
        failures = _check_assertions(
            config=config,
            output_text="output",
            tool_calls=["kubectl_apply"],
        )
        assert failures == []

    def test_tool_not_called_assertion(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            assertions=[EvalAssertion(type="tool-not-called", value="kubectl_delete")],
        )
        failures = _check_assertions(
            config=config,
            output_text="output",
            tool_calls=["kubectl_apply"],
        )
        assert failures == []

    def test_multiple_failures(self):
        config = EvalConfig(
            name="test",
            prompt="test",
            expected_tools=["kubectl_apply"],
            forbidden_tools=["kubectl_delete"],
            assertions=[EvalAssertion(type="output-contains", value="deployed")],
        )
        failures = _check_assertions(
            config=config,
            output_text="error",
            tool_calls=["kubectl_delete"],
        )
        # Expected tool missing + forbidden tool called + output assertion
        assert len(failures) == 3

    def test_judge_assertion_skipped_without_llm(self):
        """Judge assertions should gracefully skip when no LLM is available."""
        config = EvalConfig(
            name="test",
            prompt="test",
            assertions=[EvalAssertion(type="judge", criteria="Output is correct")],
        )
        # Without OPENROUTER_API_KEY or ANTHROPIC_API_KEY, judge should be skipped
        failures = _check_assertions(
            config=config,
            output_text="some output",
            tool_calls=[],
        )
        # No failure expected — judge skipped when no LLM available
        assert failures == []


class TestMockMCPServer:
    def test_server_starts_and_stops(self):
        from agentura_sdk.testing.mock_mcp_server import MockMCPServer

        mock_tools = {"test_tool": MockToolConfig(response="hello")}
        with MockMCPServer(mock_tools) as server:
            import urllib.request
            resp = urllib.request.urlopen(f"{server.url}/health")
            assert resp.status == 200

    def test_list_tools(self):
        from agentura_sdk.testing.mock_mcp_server import MockMCPServer

        mock_tools = {
            "kubectl_apply": MockToolConfig(response="created"),
            "kubectl_get": MockToolConfig(response="running"),
        }
        with MockMCPServer(mock_tools) as server:
            import urllib.request
            resp = urllib.request.urlopen(f"{server.url}/tools")
            tools = json.loads(resp.read())
            names = [t["name"] for t in tools]
            assert "kubectl_apply" in names
            assert "kubectl_get" in names

    def test_call_tool_returns_canned_response(self):
        from agentura_sdk.testing.mock_mcp_server import MockMCPServer

        mock_tools = {"kubectl_apply": MockToolConfig(response="deployment created")}
        with MockMCPServer(mock_tools) as server:
            import urllib.request
            req = urllib.request.Request(
                f"{server.url}/tools/call",
                data=json.dumps({"name": "kubectl_apply", "arguments": {}}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req)
            data = json.loads(resp.read())
            assert "deployment created" in data["content"][0]["text"]

    def test_tracks_tool_calls(self):
        from agentura_sdk.testing.mock_mcp_server import MockMCPServer

        mock_tools = {"my_tool": MockToolConfig(response="ok")}
        with MockMCPServer(mock_tools) as server:
            import urllib.request
            req = urllib.request.Request(
                f"{server.url}/tools/call",
                data=json.dumps({"name": "my_tool", "arguments": {"key": "val"}}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req)

            assert len(server.calls) == 1
            assert server.calls[0].tool_name == "my_tool"
            assert server.call_names == ["my_tool"]
