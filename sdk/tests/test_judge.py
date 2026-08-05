"""Tests for independent model evaluation (judge)."""

from __future__ import annotations

import pytest

from agentura_sdk.runner.judge import build_judge_prompt, parse_judge_response
from agentura_sdk.types import JudgeConfig


class TestBuildJudgePrompt:
    def test_includes_rubric(self):
        prompt = build_judge_prompt(
            rubric="Score 1-5: accuracy, grounding in code",
            output_text="some output",
        )
        assert "accuracy, grounding in code" in prompt

    def test_includes_output(self):
        prompt = build_judge_prompt(
            rubric="Check quality",
            output_text="Hello world output",
        )
        assert "Hello world output" in prompt

    def test_truncates_long_output(self):
        long_output = "x" * 5000
        prompt = build_judge_prompt(rubric="Check", output_text=long_output)
        # Output should be truncated to 4000 chars
        assert len(prompt) < 5000 + 500  # prompt overhead

    def test_includes_scoring_instructions(self):
        prompt = build_judge_prompt(rubric="Check", output_text="data")
        assert "SCORE:" in prompt
        assert "REASONING:" in prompt
        assert "1-5" in prompt

    def test_no_tool_evidence_by_default(self):
        prompt = build_judge_prompt(rubric="rubric", output_text="out")
        assert "Objective Evidence" not in prompt

    def test_includes_tool_evidence_when_provided(self):
        prompt = build_judge_prompt(
            rubric="rubric", output_text="out", tool_evidence="tests: 3 passed"
        )
        assert "Objective Evidence" in prompt
        assert "3 passed" in prompt


class TestRunJudgeTool:
    def test_success_output(self):
        import asyncio

        from agentura_sdk.runner.judge import run_judge_tool

        result = asyncio.run(run_judge_tool("echo hello"))
        assert "hello" in result
        assert "exit 0" in result

    def test_nonzero_exit(self):
        import asyncio

        from agentura_sdk.runner.judge import run_judge_tool

        result = asyncio.run(run_judge_tool("false"))
        assert "exit 1" in result

    def test_bad_command_does_not_raise(self):
        import asyncio

        from agentura_sdk.runner.judge import run_judge_tool

        result = asyncio.run(run_judge_tool("this_command_does_not_exist_xyz"))
        assert isinstance(result, str)


class TestParseJudgeResponse:
    def test_valid_score_and_reasoning(self):
        score, reasoning = parse_judge_response("SCORE: 4.2\nREASONING: good")
        assert score == 4.2
        assert reasoning == "good"

    def test_integer_score(self):
        score, reasoning = parse_judge_response("SCORE: 3\nREASONING: acceptable work")
        assert score == 3.0
        assert reasoning == "acceptable work"

    def test_missing_score_returns_none(self):
        score, reasoning = parse_judge_response("No score here, just text")
        assert score is None
        assert "No score here" in reasoning

    def test_non_numeric_score_returns_none(self):
        score, reasoning = parse_judge_response("SCORE: excellent\nREASONING: great")
        assert score is None
        assert reasoning == "great"

    def test_multiline_reasoning(self):
        text = "SCORE: 4.0\nREASONING: The output is well-structured.\nIt covers all dimensions."
        score, reasoning = parse_judge_response(text)
        assert score == 4.0
        assert "well-structured" in reasoning
        assert "all dimensions" in reasoning

    def test_whitespace_handling(self):
        score, reasoning = parse_judge_response("  SCORE: 3.5\n  REASONING: ok  ")
        assert score == 3.5
        assert reasoning == "ok"

    def test_case_insensitive(self):
        score, reasoning = parse_judge_response("score: 2.0\nreasoning: below par")
        assert score == 2.0
        assert reasoning == "below par"

    def test_score_only_no_reasoning(self):
        score, reasoning = parse_judge_response("SCORE: 5.0")
        assert score == 5.0
        # No REASONING: line, so reasoning falls back to raw text
        assert "SCORE" in reasoning

    def test_below_threshold_detected(self):
        """Score below threshold should be detectable by caller."""
        score, reasoning = parse_judge_response("SCORE: 2.0\nREASONING: poor quality")
        assert score is not None
        threshold = 3.0
        assert score < threshold

    def test_at_threshold_passes(self):
        score, _ = parse_judge_response("SCORE: 3.0\nREASONING: meets minimum")
        assert score is not None
        assert score >= 3.0

    def test_empty_response(self):
        score, reasoning = parse_judge_response("")
        assert score is None
        assert reasoning == ""


class TestJudgeConfig:
    def test_defaults(self):
        config = JudgeConfig()
        assert config.enabled is False
        assert config.rubric == ""
        assert config.model == ""
        assert config.score_threshold == 3.0

    def test_custom_values(self):
        config = JudgeConfig(
            enabled=True,
            rubric="accuracy, completeness",
            model="anthropic/claude-sonnet-4-6",
            score_threshold=4.0,
        )
        assert config.enabled is True
        assert config.rubric == "accuracy, completeness"
        assert config.model == "anthropic/claude-sonnet-4-6"
        assert config.score_threshold == 4.0

    def test_serialization_roundtrip(self):
        config = JudgeConfig(
            enabled=True,
            rubric="test rubric",
            model="anthropic/claude-sonnet-4-6",
            score_threshold=3.5,
        )
        data = config.model_dump()
        restored = JudgeConfig(**data)
        assert restored == config
