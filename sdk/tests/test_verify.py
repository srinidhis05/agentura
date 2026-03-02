"""Tests for self-critique evaluator loop (DEC-069)."""

from __future__ import annotations

import pytest

from agentura_sdk.runner.verify import build_verify_prompt, parse_verify_response


class TestBuildVerifyPrompt:
    def test_includes_criteria(self):
        prompt = build_verify_prompt(
            criteria=["Output is valid JSON", "Contains a summary field"],
            output_text='{"summary": "done"}',
        )
        assert "Output is valid JSON" in prompt
        assert "Contains a summary field" in prompt

    def test_includes_output(self):
        prompt = build_verify_prompt(
            criteria=["Check something"],
            output_text="Hello world output",
        )
        assert "Hello world output" in prompt

    def test_truncates_long_output(self):
        long_output = "x" * 5000
        prompt = build_verify_prompt(criteria=["Check"], output_text=long_output)
        # Output should be truncated to 4000 chars
        assert len(prompt) < 5000 + 500  # prompt overhead

    def test_includes_protocol_instructions(self):
        prompt = build_verify_prompt(criteria=["Check"], output_text="data")
        assert "VERIFIED:" in prompt
        assert "ISSUES:" in prompt


class TestParseVerifyResponse:
    def test_verified_response(self):
        passed, issues = parse_verify_response("VERIFIED: All criteria are met.")
        assert passed is True
        assert issues == []

    def test_verified_case_insensitive(self):
        passed, issues = parse_verify_response("verified: looks good")
        assert passed is True
        assert issues == []

    def test_issues_single_line(self):
        passed, issues = parse_verify_response("ISSUES: Output missing required field")
        assert passed is False
        assert len(issues) == 1
        assert "Output missing required field" in issues[0]

    def test_issues_numbered_list(self):
        text = """ISSUES:
1. Output is not valid JSON
2. Missing summary field
3. No deployment URL provided"""
        passed, issues = parse_verify_response(text)
        assert passed is False
        assert len(issues) == 3
        assert "Output is not valid JSON" in issues[0]
        assert "Missing summary field" in issues[1]
        assert "No deployment URL provided" in issues[2]

    def test_issues_bulleted_list(self):
        text = """ISSUES:
- Response lacks error handling
- No retry logic"""
        passed, issues = parse_verify_response(text)
        assert passed is False
        assert len(issues) == 2
        assert "Response lacks error handling" in issues[0]

    def test_ambiguous_response_treated_as_issues(self):
        passed, issues = parse_verify_response("The output has some problems.")
        assert passed is False
        assert len(issues) == 1

    def test_empty_response_treated_as_issues(self):
        passed, issues = parse_verify_response("")
        assert passed is False

    def test_whitespace_handling(self):
        passed, issues = parse_verify_response("  VERIFIED: all good  ")
        assert passed is True
        assert issues == []

    def test_issues_with_dash_numbered(self):
        text = """ISSUES:
1) First issue found
2) Second issue found"""
        passed, issues = parse_verify_response(text)
        assert passed is False
        assert len(issues) == 2
