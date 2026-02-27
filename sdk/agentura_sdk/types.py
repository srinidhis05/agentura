"""Core SDK types — compose with agents/core/types.py, don't duplicate."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SkillRole(str, Enum):
    MANAGER = "manager"
    SPECIALIST = "specialist"
    FIELD = "field"
    AGENT = "agent"


class SkillLanguage(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"


# --- Skill metadata (parsed from SKILL.md frontmatter) ---

class SkillMetadata(BaseModel):
    """Parsed from SKILL.md YAML frontmatter."""
    name: str
    role: SkillRole
    domain: str
    trigger: str = "manual"
    model: str = "anthropic/claude-sonnet-4.5"
    cost_budget_per_execution: str = "$0.10"
    timeout: str = "60s"
    routes_to: list[dict[str, str]] = Field(default_factory=list)


# --- Agent/sandbox config ---

class SandboxConfig(BaseModel):
    """Sandbox settings for agent-role skills."""
    template: str = "base"
    timeout: int = 300
    max_iterations: int = 50
    cpu: int = 2
    memory: int = 512
    backend: str = ""


class AgentIteration(BaseModel):
    """Single tool-call iteration within an agent execution loop."""
    iteration: int
    tool_name: str
    tool_input: dict[str, Any]
    tool_output: str
    timestamp: str


# --- Domain config (parsed from agentura.config.yaml) ---

class SkillRef(BaseModel):
    """Skill reference within domain config."""
    name: str
    path: str
    role: SkillRole
    model: str = "anthropic/claude-sonnet-4.5"
    cost_budget: str = "$0.10"
    triggers: list[dict[str, Any]] = Field(default_factory=list)


class RoutingRule(BaseModel):
    when: dict[str, Any]
    then: dict[str, Any]


class GuardrailsConfig(BaseModel):
    budget: dict[str, Any] = Field(default_factory=dict)
    human_in_loop: dict[str, Any] = Field(default_factory=dict)
    rate_limits: dict[str, Any] = Field(default_factory=dict)


class ObservabilityConfig(BaseModel):
    metrics: list[dict[str, Any]] = Field(default_factory=list)
    logs: dict[str, Any] = Field(default_factory=dict)
    traces: dict[str, Any] = Field(default_factory=dict)


class FeedbackConfig(BaseModel):
    capture_corrections: bool = True
    auto_generate_tests: bool = True
    test_framework: str = "deepeval"
    learning_strategy: dict[str, str] = Field(default_factory=dict)
    regression_tests: dict[str, Any] = Field(default_factory=dict)


class McpToolRef(BaseModel):
    server: str
    tools: list[str]


class DomainConfig(BaseModel):
    """Parsed from agentura.config.yaml — the domain-level orchestration file."""
    name: str
    description: str = ""
    owner: str = ""


class SkillConfig(BaseModel):
    """Full parsed agentura.config.yaml."""
    domain: DomainConfig
    skills: list[SkillRef] = Field(default_factory=list)
    routing: list[RoutingRule] = Field(default_factory=list)
    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    feedback: FeedbackConfig = Field(default_factory=FeedbackConfig)
    mcp_tools: list[McpToolRef] = Field(default_factory=list)


# --- Runtime types (SkillContext → SkillResult contract from DEC-005) ---

class SkillContext(BaseModel):
    """Input to a skill execution. All handlers implement: SkillContext → SkillResult."""
    skill_name: str
    domain: str
    role: SkillRole
    model: str = "anthropic/claude-sonnet-4.5"
    system_prompt: str = ""
    input_data: dict[str, Any] = Field(default_factory=dict)
    routed_context: dict[str, Any] = Field(default_factory=dict)
    mcp_tools: list[str] = Field(default_factory=list)
    mcp_bindings: list[dict] = Field(default_factory=list)
    sandbox_config: Optional[SandboxConfig] = None


class SkillResult(BaseModel):
    """Output from a skill execution."""
    skill_name: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    reasoning_trace: list[str] = Field(default_factory=list)
    model_used: str = ""
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    route_to: Optional[str] = None
    context_for_next: dict[str, Any] = Field(default_factory=dict)
    approval_required: bool = False
    pending_action: str = ""


# --- Service indexer types ---

class TechStack(BaseModel):
    """Detected technology stack for a service repository."""
    languages: list[str] = Field(default_factory=list)
    build_tool: str = ""
    frameworks: list[str] = Field(default_factory=list)
    test_framework: str = ""
    package_manager: str = ""


class ModuleInfo(BaseModel):
    """A logical module within a service (package, directory, etc.)."""
    path: str
    purpose: str = ""
    files_count: int = 0
    lines_count: int = 0


class ServiceIndex(BaseModel):
    """Result of indexing a service repository."""
    service_name: str
    repo_path: str
    output_dir: str
    tech_stack: TechStack
    files_generated: list[str] = Field(default_factory=list)


class MappedSkill(BaseModel):
    """An ai-velocity skill mapped to a service task."""
    name: str
    path: str
    content: str
    truncated: bool = False
