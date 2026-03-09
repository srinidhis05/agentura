"""Workflow eval types — Pydantic models for eval configs and results (DEC-070)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MockToolConfig(BaseModel):
    """Canned response for a mocked MCP tool."""
    response: str = ""


class EvalAssertion(BaseModel):
    """A single assertion to check against eval output."""
    type: str  # "output-contains", "judge", "tool-called", "tool-not-called"
    value: str = ""
    criteria: str = ""


class EvalConfig(BaseModel):
    """Complete eval configuration loaded from evals/*.yaml."""
    name: str
    prompt: str
    input_data: dict = Field(default_factory=dict)
    mock_tools: dict[str, MockToolConfig] = Field(default_factory=dict)
    expected_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    assertions: list[EvalAssertion] = Field(default_factory=list)
    max_retries: int = 3


class EvalResult(BaseModel):
    """Result of running a single eval."""
    name: str
    passed: bool
    attempts: int = 1
    failures: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    output: str = ""
