"""Tests for memory synthesis from execution logs (DEC-068)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agentura_sdk.cortex.synthesizer import (
    SynthesisCandidate,
    _build_logs_section,
    _parse_candidates,
)


class TestParseCandidates:
    def test_parse_valid_json_array(self):
        raw = """[
            {"rule": "Always use NodePort", "applies_when": "creating services", "pattern_count": 3, "skill": "dev/deployer"},
            {"rule": "Pin base images", "applies_when": "selecting Docker images", "pattern_count": 5, "skill": "dev/app-builder"}
        ]"""
        result = _parse_candidates(raw)
        assert len(result) == 2
        assert result[0].rule == "Always use NodePort"
        assert result[1].pattern_count == 5

    def test_parse_markdown_wrapped_json(self):
        raw = """Here are the patterns:
```json
[{"rule": "Check pod status", "applies_when": "deploying", "pattern_count": 2, "skill": "dev/deployer"}]
```"""
        result = _parse_candidates(raw)
        assert len(result) == 1

    def test_parse_empty_array(self):
        result = _parse_candidates("[]")
        assert result == []

    def test_parse_invalid_json(self):
        result = _parse_candidates("this is not json")
        assert result == []

    def test_parse_missing_fields(self):
        raw = '[{"rule": "Some rule"}]'
        result = _parse_candidates(raw)
        assert len(result) == 1
        assert result[0].applies_when == ""
        assert result[0].pattern_count == 1


class TestBuildLogsSection:
    def test_builds_skill_sections(self):
        by_skill = {
            "dev/deployer": [
                {"timestamp": "2026-03-01T10:00:00", "output_summary": {"error": "pod crash"}},
                {"timestamp": "2026-03-01T11:00:00", "output_summary": {"error": "timeout"}},
            ],
        }
        corrections = {
            "dev/deployer": [
                {"user_correction": "Use NodePort instead of ClusterIP"},
            ],
        }
        result = _build_logs_section(by_skill, corrections)
        assert "dev/deployer" in result
        assert "2 failures" in result
        assert "pod crash" in result
        assert "NodePort" in result

    def test_truncates_long_errors(self):
        by_skill = {
            "dev/deployer": [
                {"timestamp": "2026-03-01", "output_summary": {"error": "x" * 500}},
            ],
        }
        result = _build_logs_section(by_skill, {})
        # Error should be truncated to 200 chars
        assert len(result) < 600

    def test_limits_entries_per_skill(self):
        by_skill = {
            "dev/deployer": [
                {"timestamp": f"2026-03-01T{i:02d}:00:00", "output_summary": {"error": f"err-{i}"}}
                for i in range(30)
            ],
        }
        result = _build_logs_section(by_skill, {})
        # Should only include first 20
        assert "err-19" in result
        assert "err-20" not in result
