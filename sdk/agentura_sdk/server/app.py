"""Agentura Skill Executor — FastAPI server wrapping SDK functions."""

import json as _json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env before anything reads env vars (so DATABASE_URL, API keys are available)
load_dotenv(Path.cwd() / ".env")

import yaml
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from agentura_sdk.runner.skill_loader import load_skill_md
from agentura_sdk.types import SandboxConfig, SkillContext, SkillResult, SkillRole

SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", "/skills"))
KNOWLEDGE_DIR = Path(os.environ.get("AGENTURA_KNOWLEDGE_DIR") or str(".agentura"))

# Directories to skip when scanning for skills
SKIP_DIRS = {"shared", "__pycache__", "node_modules", ".git"}

# TTL caches to avoid repeated file reads within the same request cycle
_CACHE_TTL = 5.0  # seconds
_knowledge_cache: dict[str, tuple[float, dict]] = {}
_domain_config_cache: dict[str, tuple[float, dict]] = {}

app = FastAPI(title="Agentura Skill Executor", version="0.1.0")

# Auth middleware — validates X-User-ID + X-Domain-Scope from gateway
from agentura_sdk.server.auth import AuthMiddleware, get_auth_required

app.add_middleware(AuthMiddleware, required=get_auth_required())

# CORS — allow frontend dev server
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_domain_scope(request: Request) -> set[str] | None:
    """FastAPI dependency — extract allowed domains from auth middleware state.

    Returns None (unrestricted) when domain_scope is '*' or not set.
    Returns a set of domain names otherwise.
    """
    scope = getattr(getattr(request, "state", None), "domain_scope", "*")
    if scope == "*" or not scope:
        return None
    return {d.strip() for d in scope.split(",") if d.strip()}


def _filter_by_domain(entries: list[dict], allowed: set[str] | None, key: str = "skill") -> list[dict]:
    """Filter entries to only those matching allowed domains."""
    if allowed is None:
        return entries
    return [e for e in entries if e.get(key, "").split("/")[0] in allowed]


class ExecuteRequest(BaseModel):
    input_data: dict[str, Any] = Field(default_factory=dict)
    model_override: str | None = None
    dry_run: bool = False


class CorrectRequest(BaseModel):
    execution_id: str
    correction: str


class SkillInfo(BaseModel):
    domain: str
    name: str
    role: str
    model: str
    trigger: str
    description: str = ""
    cost_budget: str = ""
    timeout: str = ""
    mcp_tools: list[str] = Field(default_factory=list)
    domain_description: str = ""
    domain_owner: str = ""
    guardrails_count: int = 0
    corrections_count: int = 0
    # Lifecycle fields (K8s pod-like)
    deploy_status: str = "active"  # active | canary | shadow | disabled
    health: str = "healthy"  # healthy | degraded | failing | unknown
    version: str = "v1"
    last_deployed: str = ""
    executions_total: int = 0
    accept_rate: float = 0.0
    # Display metadata (for dashboard visualization)
    display_title: str = ""
    display_subtitle: str = ""
    display_avatar: str = ""
    display_color: str = ""
    display_tags: list[str] = Field(default_factory=list)


class SkillDetail(BaseModel):
    """Full detail for a single skill — returned by GET /api/v1/skills/{domain}/{skill_name}."""
    domain: str
    name: str
    role: str
    model: str
    trigger: str
    description: str = ""
    cost_budget: str = ""
    timeout: str = ""
    mcp_tools: list[str] = Field(default_factory=list)
    domain_description: str = ""
    domain_owner: str = ""
    guardrails_count: int = 0
    corrections_count: int = 0
    # Lifecycle
    deploy_status: str = "active"
    health: str = "healthy"
    version: str = "v1"
    last_deployed: str = ""
    executions_total: int = 0
    accept_rate: float = 0.0
    # Display metadata
    display_title: str = ""
    display_subtitle: str = ""
    display_avatar: str = ""
    display_color: str = ""
    display_tags: list[str] = Field(default_factory=list)
    # Detail-only
    task_description: str = ""
    input_schema: str = ""
    output_schema: str = ""
    skill_body: str = ""
    skill_guardrails: list[str] = Field(default_factory=list)
    triggers: list[dict[str, Any]] = Field(default_factory=list)
    feedback_enabled: bool = False


def _extract_h1(content: str) -> str:
    """Extract first H1 title from markdown body."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_section(content: str, heading: str) -> str:
    """Extract the body of a ## heading section until the next ## or end."""
    pattern = rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_guardrail_bullets(content: str) -> list[str]:
    """Extract bullet points from ## Guardrails section."""
    section = _extract_section(content, "Guardrails")
    if not section:
        return []
    return [line.lstrip("- ").strip() for line in section.splitlines() if line.strip().startswith("-")]


def _count_guardrails(domain_dir: Path) -> int:
    """Count GRD-NNN entries in domain-level GUARDRAILS.md."""
    grd_file = domain_dir / "GUARDRAILS.md"
    if not grd_file.exists():
        return 0
    return len(re.findall(r"##\s+GRD-\d+", grd_file.read_text()))


def _count_corrections(skill_dir: Path) -> int:
    """Count test entries in tests/generated/corrections.yaml."""
    corr_file = skill_dir / "tests" / "generated" / "corrections.yaml"
    if not corr_file.exists():
        return 0
    try:
        data = yaml.safe_load(corr_file.read_text())
        return len(data.get("tests", [])) if data else 0
    except Exception:
        return 0


def _load_domain_config(domain_dir: Path) -> dict[str, Any]:
    """Load and cache domain agentura.config.yaml data (cached with TTL). Returns empty dict on failure."""
    key = str(domain_dir)
    now = time.time()
    if key in _domain_config_cache:
        ts, data = _domain_config_cache[key]
        if now - ts < _CACHE_TTL:
            return data

    # Check all skill subdirs for agentura.config.yaml (it's at skill level)
    for child in domain_dir.iterdir():
        cfg_path = child / "agentura.config.yaml"
        if cfg_path.exists():
            try:
                result = yaml.safe_load(cfg_path.read_text()) or {}
                _domain_config_cache[key] = (now, result)
                return result
            except Exception:
                pass
    _domain_config_cache[key] = (now, {})
    return {}


def _compute_skill_lifecycle(skill_path: str) -> dict:
    """Compute deploy_status, health, accept_rate, executions_total from execution history."""
    exec_data = _load_knowledge_file("episodic_memory.json")
    entries = [e for e in exec_data.get("entries", []) if e.get("skill") == skill_path]
    total = len(entries)
    accepted = sum(1 for e in entries if e.get("outcome") == "accepted")
    rate = round(accepted / total, 2) if total else 0.0

    # Derive health from recent accept rate
    if total == 0:
        health = "unknown"
    elif rate >= 0.8:
        health = "healthy"
    elif rate >= 0.5:
        health = "degraded"
    else:
        health = "failing"

    return {
        "executions_total": total,
        "accept_rate": rate,
        "health": health,
    }


def _build_skill_info(skill_dir: Path, domain_dir: Path) -> SkillInfo | None:
    """Build an enriched SkillInfo from skill files."""
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        return None
    try:
        loaded = load_skill_md(skill_md_path, include_reflexions=False)
    except Exception:
        return None

    body = loaded.raw_content
    config = _load_domain_config(domain_dir)
    domain_cfg = config.get("domain", {})
    mcp_tools = [t.get("server", "") for t in config.get("mcp_tools", [])]

    # Lifecycle: derive from execution history + file metadata
    skill_path = f"{loaded.metadata.domain}/{loaded.metadata.name}"
    lifecycle = _compute_skill_lifecycle(skill_path)

    # Version from file mtime
    from datetime import datetime, timezone
    mtime = skill_md_path.stat().st_mtime
    last_deployed = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

    # Deploy status from config (look for canary/shadow markers)
    deploy_status = "active"
    for s in config.get("skills", []):
        if s.get("name") == loaded.metadata.name:
            deploy_status = s.get("deploy_status", "active")
            break

    # Display metadata from skill-level config
    skill_cfg_path = skill_dir / "agentura.config.yaml"
    display = {}
    if skill_cfg_path.exists():
        try:
            skill_cfg = yaml.safe_load(skill_cfg_path.read_text()) or {}
            display = skill_cfg.get("display", {})
        except Exception:
            pass

    # Auto-generate display fields if not configured
    skill_name = loaded.metadata.name
    display_title = display.get("title", "") or skill_name.replace("-", " ").title()
    display_avatar = display.get("avatar", "") or skill_name[:2].upper()

    return SkillInfo(
        domain=loaded.metadata.domain,
        name=loaded.metadata.name,
        role=loaded.metadata.role.value,
        model=loaded.metadata.model,
        trigger=loaded.metadata.trigger,
        description=_extract_h1(body),
        cost_budget=loaded.metadata.cost_budget_per_execution,
        timeout=loaded.metadata.timeout,
        mcp_tools=mcp_tools,
        domain_description=domain_cfg.get("description", ""),
        domain_owner=domain_cfg.get("owner", ""),
        guardrails_count=_count_guardrails(domain_dir),
        corrections_count=_count_corrections(skill_dir),
        deploy_status=deploy_status,
        health=lifecycle["health"],
        version="v1",
        last_deployed=last_deployed,
        executions_total=lifecycle["executions_total"],
        accept_rate=lifecycle["accept_rate"],
        display_title=display_title,
        display_subtitle=display.get("subtitle", ""),
        display_avatar=display_avatar,
        display_color=display.get("color", ""),
        display_tags=display.get("tags", []),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/v1/triggers")
def list_triggers():
    """Return all skill trigger definitions for the gateway cron scheduler."""
    results: list[dict[str, Any]] = []
    if not SKILLS_DIR.exists():
        return results

    for domain_dir in sorted(SKILLS_DIR.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("."):
            continue
        for skill_dir in sorted(domain_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith(".") or skill_dir.name in SKIP_DIRS:
                continue
            cfg_path = skill_dir / "agentura.config.yaml"
            if not cfg_path.exists():
                continue
            try:
                cfg = yaml.safe_load(cfg_path.read_text()) or {}
            except Exception:
                continue
            for s in cfg.get("skills", []):
                triggers = s.get("triggers", [])
                if triggers:
                    results.append({
                        "domain": domain_dir.name,
                        "skill": s.get("name", skill_dir.name),
                        "triggers": triggers,
                    })
    return results


@app.get("/api/v1/skills", response_model=list[SkillInfo])
def list_skills():
    """List all available skills by scanning SKILLS_DIR."""
    skills: list[SkillInfo] = []
    if not SKILLS_DIR.exists():
        return skills

    for domain_dir in sorted(SKILLS_DIR.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("."):
            continue
        for skill_dir in sorted(domain_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith(".") or skill_dir.name in SKIP_DIRS:
                continue
            info = _build_skill_info(skill_dir, domain_dir)
            if info:
                skills.append(info)
    return skills


@app.get("/api/v1/skills/{domain}/{skill_name}", response_model=SkillDetail)
def get_skill(domain: str, skill_name: str):
    """Return full detail for a single skill."""
    skill_dir = SKILLS_DIR / domain / skill_name
    domain_dir = SKILLS_DIR / domain
    skill_md_path = skill_dir / "SKILL.md"

    if not skill_dir.exists() or not skill_md_path.exists():
        raise HTTPException(status_code=404, detail=f"Skill not found: {domain}/{skill_name}")

    try:
        loaded = load_skill_md(skill_md_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    body = loaded.raw_content
    config = _load_domain_config(domain_dir)
    domain_cfg = config.get("domain", {})
    mcp_tools = [t.get("server", "") for t in config.get("mcp_tools", [])]
    feedback_cfg = config.get("feedback", {})

    # Find triggers for this specific skill
    triggers: list[dict[str, Any]] = []
    for s in config.get("skills", []):
        if s.get("name") == skill_name:
            triggers = s.get("triggers", [])
            break

    # Lifecycle
    skill_path = f"{domain}/{skill_name}"
    lifecycle = _compute_skill_lifecycle(skill_path)
    from datetime import datetime, timezone
    mtime = skill_md_path.stat().st_mtime
    last_deployed = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

    deploy_status = "active"
    for s in config.get("skills", []):
        if s.get("name") == skill_name:
            deploy_status = s.get("deploy_status", "active")
            break

    # Display metadata from skill-level config
    skill_config_path = skill_dir / "agentura.config.yaml"
    display = {}
    if skill_config_path.exists():
        try:
            skill_cfg_detail = yaml.safe_load(skill_config_path.read_text()) or {}
            display = skill_cfg_detail.get("display", {})
        except Exception:
            pass

    display_title = display.get("title", "") or skill_name.replace("-", " ").title()
    display_avatar = display.get("avatar", "") or skill_name[:2].upper()

    return SkillDetail(
        domain=loaded.metadata.domain,
        name=loaded.metadata.name,
        role=loaded.metadata.role.value,
        model=loaded.metadata.model,
        trigger=loaded.metadata.trigger,
        description=_extract_h1(body),
        cost_budget=loaded.metadata.cost_budget_per_execution,
        timeout=loaded.metadata.timeout,
        mcp_tools=mcp_tools,
        domain_description=domain_cfg.get("description", ""),
        domain_owner=domain_cfg.get("owner", ""),
        guardrails_count=_count_guardrails(domain_dir),
        corrections_count=_count_corrections(skill_dir),
        deploy_status=deploy_status,
        health=lifecycle["health"],
        version="v1",
        last_deployed=last_deployed,
        executions_total=lifecycle["executions_total"],
        accept_rate=lifecycle["accept_rate"],
        display_title=display_title,
        display_subtitle=display.get("subtitle", ""),
        display_avatar=display_avatar,
        display_color=display.get("color", ""),
        display_tags=display.get("tags", []),
        task_description=_extract_section(body, "Task"),
        input_schema=_extract_section(body, "Input Format") or _extract_section(body, "Context You'll Receive"),
        output_schema=_extract_section(body, "Output Format"),
        skill_body=loaded.system_prompt,
        skill_guardrails=_extract_guardrail_bullets(body),
        triggers=triggers,
        feedback_enabled=feedback_cfg.get("capture_corrections", False),
    )


@app.post(
    "/api/v1/skills/{domain}/{skill_name}/execute",
    response_model=SkillResult,
)
async def execute(domain: str, skill_name: str, req: ExecuteRequest):
    """Execute a skill — mirrors cli/run.py logic."""
    root = SKILLS_DIR / domain / skill_name
    skill_md_path = root / "SKILL.md"

    if not root.exists() or not skill_md_path.exists():
        raise HTTPException(status_code=404, detail=f"Skill not found: {domain}/{skill_name}")

    skill_md = load_skill_md(skill_md_path)

    # Build input: explicit > fixture > empty
    input_data = req.input_data
    if not input_data:
        fixture = root / "fixtures" / "sample_input.json"
        if fixture.exists():
            import json
            input_data = json.loads(fixture.read_text())

    model = req.model_override or skill_md.metadata.model

    # Compose system prompt: WORKSPACE + DOMAIN + Reflexion + SKILL
    prompt_parts = []
    if skill_md.workspace_context:
        prompt_parts.append(skill_md.workspace_context)
    if skill_md.domain_context:
        prompt_parts.append(skill_md.domain_context)
    if skill_md.reflexion_context:
        prompt_parts.append(skill_md.reflexion_context)
    prompt_parts.append(skill_md.system_prompt)
    composed_prompt = "\n\n---\n\n".join(prompt_parts)

    # Parse sandbox config for agent-role skills
    sandbox_config = None
    if skill_md.metadata.role == SkillRole.AGENT:
        sandbox_config = SandboxConfig()
        skill_config_path = root / "agentura.config.yaml"
        if skill_config_path.exists():
            try:
                skill_cfg_raw = yaml.safe_load(skill_config_path.read_text()) or {}
                sandbox_raw = skill_cfg_raw.get("sandbox", {})
                if sandbox_raw:
                    sandbox_config = SandboxConfig(**sandbox_raw)
            except Exception:
                pass

    ctx = SkillContext(
        skill_name=skill_md.metadata.name,
        domain=skill_md.metadata.domain,
        role=skill_md.metadata.role,
        model=model,
        system_prompt=composed_prompt,
        input_data=input_data,
        sandbox_config=sandbox_config,
    )

    if req.dry_run:
        return SkillResult(
            skill_name=ctx.skill_name,
            success=True,
            output={
                "dry_run": True,
                "skill": ctx.skill_name,
                "domain": ctx.domain,
                "model": ctx.model,
                "prompt_length": len(ctx.system_prompt),
                "input_keys": list(input_data.keys()),
            },
        )

    from agentura_sdk.runner.local_runner import execute_skill

    result = await execute_skill(ctx)

    # Check human-in-the-loop approval requirement
    skill_config_path = root / "agentura.config.yaml"
    if skill_config_path.exists():
        try:
            skill_cfg = yaml.safe_load(skill_config_path.read_text()) or {}
            guardrails = skill_cfg.get("guardrails", {})
            hitl = guardrails.get("human_in_loop", {}) if isinstance(guardrails, dict) else {}
            if hitl.get("require_approval", False):
                result.approval_required = True
                result.pending_action = hitl.get("approval_prompt", "Review and approve this output")
        except Exception:
            pass

    # If approval is required, update the execution entry outcome to pending_approval
    if result.approval_required:
        _update_execution_outcome_to_pending_approval(domain, skill_name)

    return result


@app.post("/api/v1/skills/{domain}/{skill_name}/execute-stream")
async def execute_stream(domain: str, skill_name: str, req: ExecuteRequest):
    """SSE streaming endpoint for agent-role skill executions.

    Yields AgentIteration events as the agent works, then a final SkillResult.
    Non-agent skills return 400.
    """
    from starlette.responses import StreamingResponse

    from agentura_sdk.runner.agent_executor import execute_agent_streaming
    from agentura_sdk.types import AgentIteration as AgentIterationType

    root = SKILLS_DIR / domain / skill_name
    skill_md_path = root / "SKILL.md"

    if not root.exists() or not skill_md_path.exists():
        raise HTTPException(status_code=404, detail=f"Skill not found: {domain}/{skill_name}")

    skill_md = load_skill_md(skill_md_path)

    if skill_md.metadata.role != SkillRole.AGENT:
        raise HTTPException(status_code=400, detail="SSE streaming is only available for agent-role skills")

    input_data = req.input_data
    if not input_data:
        fixture = root / "fixtures" / "sample_input.json"
        if fixture.exists():
            import json
            input_data = json.loads(fixture.read_text())

    model = req.model_override or skill_md.metadata.model

    # Parse sandbox config from skill-level agentura.config.yaml
    sandbox_config = SandboxConfig()
    skill_config_path = root / "agentura.config.yaml"
    if skill_config_path.exists():
        try:
            skill_cfg = yaml.safe_load(skill_config_path.read_text()) or {}
            sandbox_raw = skill_cfg.get("sandbox", {})
            if sandbox_raw:
                sandbox_config = SandboxConfig(**sandbox_raw)
        except Exception:
            pass

    prompt_parts = []
    if skill_md.workspace_context:
        prompt_parts.append(skill_md.workspace_context)
    if skill_md.domain_context:
        prompt_parts.append(skill_md.domain_context)
    if skill_md.reflexion_context:
        prompt_parts.append(skill_md.reflexion_context)
    prompt_parts.append(skill_md.system_prompt)
    composed_prompt = "\n\n---\n\n".join(prompt_parts)

    ctx = SkillContext(
        skill_name=skill_md.metadata.name,
        domain=skill_md.metadata.domain,
        role=skill_md.metadata.role,
        model=model,
        system_prompt=composed_prompt,
        input_data=input_data,
        sandbox_config=sandbox_config,
    )

    async def event_generator():
        async for event in execute_agent_streaming(ctx):
            if isinstance(event, AgentIterationType):
                yield f"event: iteration\ndata: {event.model_dump_json()}\n\n"
            else:
                # Final SkillResult
                yield f"event: result\ndata: {event.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/v1/skills/{domain}/{skill_name}/correct")
def correct(domain: str, skill_name: str, req: CorrectRequest):
    """Capture a correction — mirrors cli/correct.py logic.

    Full pipeline: Correction → Reflexion → Tests → Guardrails (DEC-006).
    """
    from agentura_sdk.cli.correct import (
        _generate_reflexion,
        _load_execution,
        _store_correction,
        _update_guardrails,
    )

    skill_path = f"{domain}/{skill_name}"
    skill_dir = SKILLS_DIR / domain / skill_name

    if not skill_dir.exists():
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_path}")

    execution = _load_execution(req.execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution not found: {req.execution_id}")

    correction_id = _store_correction(
        skill_path=skill_path,
        execution_id=req.execution_id,
        correction=req.correction,
        original_output=execution.get("output_summary", {}),
    )

    reflexion_id = _generate_reflexion(
        skill_path=skill_path,
        correction_id=correction_id,
        original_output=execution.get("output_summary", {}),
        correction=req.correction,
        input_data=execution.get("input_summary"),
    )

    # Test generation is best-effort in server mode
    deepeval_file = None
    promptfoo_file = None
    try:
        from agentura_sdk.testing.deepeval_runner import generate_test_from_correction
        from agentura_sdk.testing.test_generator import generate_promptfoo_test

        deepeval_file = str(generate_test_from_correction(
            skill_dir=skill_dir,
            input_data=execution.get("input_summary", {}),
            actual_output=execution.get("output_summary", {}),
            corrected_output={"correction": req.correction},
        ))
        promptfoo_file = str(generate_promptfoo_test(
            skill_dir=skill_dir,
            input_data=execution.get("input_summary", {}),
            expected_output={"correction": req.correction},
            description=f"Correction {correction_id}: {req.correction[:80]}",
        ))
    except Exception:
        pass

    # Guardrail updates (parity with CLI — was missing from server endpoint)
    guardrails_updated = False
    try:
        guardrails_updated = _update_guardrails(skill_dir, req.correction)
    except Exception:
        pass

    return {
        "correction_id": correction_id,
        "reflexion_id": reflexion_id,
        "deepeval_test": deepeval_file,
        "promptfoo_test": promptfoo_file,
        "guardrails_updated": guardrails_updated,
    }


def _update_execution_outcome_to_pending_approval(domain: str, skill_name: str) -> None:
    """Set the most recent execution for this skill to pending_approval."""
    skill_path = f"{domain}/{skill_name}"
    for p in [
        KNOWLEDGE_DIR / "episodic_memory.json",
        Path.cwd() / ".agentura" / "episodic_memory.json",
        Path("/skills") / ".agentura" / "episodic_memory.json",
    ]:
        if not p.exists():
            continue
        try:
            data = _json.loads(p.read_text())
            entries = data.get("entries", [])
            # Find the most recent entry for this skill
            for entry in reversed(entries):
                if entry.get("skill") == skill_path:
                    entry["outcome"] = "pending_approval"
                    break
            p.write_text(_json.dumps(data, indent=2))
            # Invalidate knowledge cache
            _knowledge_cache.pop("episodic_memory.json", None)
            return
        except Exception:
            continue


class ApprovalRequest(BaseModel):
    approved: bool
    reviewer_notes: str = ""


@app.post("/api/v1/executions/{execution_id}/approve")
def approve_execution(execution_id: str, req: ApprovalRequest):
    """Approve or reject a pending execution."""
    for p in [
        KNOWLEDGE_DIR / "episodic_memory.json",
        Path.cwd() / ".agentura" / "episodic_memory.json",
        Path("/skills") / ".agentura" / "episodic_memory.json",
    ]:
        if not p.exists():
            continue
        try:
            data = _json.loads(p.read_text())
            entries = data.get("entries", [])
            entry = next((e for e in entries if e.get("execution_id") == execution_id), None)
            if not entry:
                continue

            if entry.get("outcome") != "pending_approval":
                raise HTTPException(
                    status_code=409,
                    detail=f"Execution {execution_id} is not pending approval (current: {entry.get('outcome')})",
                )

            entry["outcome"] = "approved" if req.approved else "rejected"
            entry["reviewer_notes"] = req.reviewer_notes
            p.write_text(_json.dumps(data, indent=2))

            # Invalidate knowledge cache
            _knowledge_cache.pop("episodic_memory.json", None)

            return {
                "execution_id": execution_id,
                "outcome": entry["outcome"],
                "reviewer_notes": req.reviewer_notes,
            }
        except HTTPException:
            raise
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")


# ---------------------------------------------------------------------------
# Execution history + analytics
# ---------------------------------------------------------------------------

class ExecutionEntry(BaseModel):
    execution_id: str
    skill: str
    timestamp: str = ""
    input_summary: Any = None
    output_summary: Any = None
    outcome: str = "pending_review"
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    model_used: str = ""
    user_feedback: str | None = None
    correction_generated_test: bool = False
    reflexion_applied: str | None = None
    reviewer_notes: str = ""


class CorrectionEntry(BaseModel):
    correction_id: str
    execution_id: str
    skill: str
    timestamp: str = ""
    original_output: Any = None
    user_correction: str = ""


class ReflexionEntry(BaseModel):
    reflexion_id: str
    correction_id: str
    skill: str
    created_at: str = ""
    rule: str = ""
    applies_when: str = ""
    confidence: float = 0.0
    validated_by_test: bool = False


class ExecutionDetail(BaseModel):
    execution: ExecutionEntry
    corrections: list[CorrectionEntry] = Field(default_factory=list)
    reflexions: list[ReflexionEntry] = Field(default_factory=list)


class AnalyticsResponse(BaseModel):
    total_executions: int = 0
    accepted: int = 0
    corrected: int = 0
    pending_review: int = 0
    accept_rate: float = 0.0
    total_cost_usd: float = 0.0
    avg_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    total_corrections: int = 0
    total_reflexions: int = 0
    correction_to_test_rate: float = 0.0
    executions_by_skill: dict[str, int] = Field(default_factory=dict)
    cost_by_skill: dict[str, float] = Field(default_factory=dict)
    latency_by_skill: dict[str, float] = Field(default_factory=dict)
    recent_executions: list[ExecutionEntry] = Field(default_factory=list)


def _load_knowledge_file(name: str) -> dict:
    """Load a JSON file from the knowledge directory (cached with TTL)."""
    now = time.time()
    if name in _knowledge_cache:
        ts, data = _knowledge_cache[name]
        if now - ts < _CACHE_TTL:
            return data

    # Try multiple locations
    candidates = [
        KNOWLEDGE_DIR / name,
        Path.cwd() / ".agentura" / name,
        Path("/skills") / ".agentura" / name,
    ]
    for p in candidates:
        if p.exists():
            try:
                result = _json.loads(p.read_text())
                _knowledge_cache[name] = (now, result)
                return result
            except Exception:
                continue
    _knowledge_cache[name] = (now, {})
    return {}


@app.get("/api/v1/executions", response_model=list[ExecutionEntry])
def list_executions(
    skill: str | None = None,
    outcome: str | None = None,
    domains: set[str] | None = Depends(_get_domain_scope),
):
    """List execution history from episodic memory (domain-scoped)."""
    data = _load_knowledge_file("episodic_memory.json")
    entries = _filter_by_domain(data.get("entries", []), domains)

    if skill:
        entries = [e for e in entries if e.get("skill") == skill]
    if outcome:
        entries = [e for e in entries if e.get("outcome") == outcome]

    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    return [ExecutionEntry(**{k: v for k, v in e.items() if k in ExecutionEntry.model_fields}) for e in entries]


@app.get("/api/v1/executions/{execution_id}", response_model=ExecutionDetail)
def get_execution(execution_id: str, domains: set[str] | None = Depends(_get_domain_scope)):
    """Get execution detail with linked corrections and reflexions (domain-scoped)."""
    data = _load_knowledge_file("episodic_memory.json")
    entries = _filter_by_domain(data.get("entries", []), domains)
    entry = next((e for e in entries if e.get("execution_id") == execution_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")

    execution = ExecutionEntry(**{k: v for k, v in entry.items() if k in ExecutionEntry.model_fields})

    # Find linked corrections
    corr_data = _load_knowledge_file("corrections.json")
    corrections = [
        CorrectionEntry(**{k: v for k, v in c.items() if k in CorrectionEntry.model_fields})
        for c in corr_data.get("corrections", [])
        if c.get("execution_id") == execution_id
    ]

    # Find linked reflexions (via correction_ids)
    corr_ids = {c.correction_id for c in corrections}
    refl_data = _load_knowledge_file("reflexion_entries.json")
    reflexions = [
        ReflexionEntry(**{k: v for k, v in r.items() if k in ReflexionEntry.model_fields})
        for r in refl_data.get("entries", [])
        if r.get("correction_id") in corr_ids
    ]

    return ExecutionDetail(execution=execution, corrections=corrections, reflexions=reflexions)


@app.get("/api/v1/analytics", response_model=AnalyticsResponse)
def get_analytics(domains: set[str] | None = Depends(_get_domain_scope)):
    """Aggregate metrics across all executions, corrections, and reflexions (domain-scoped)."""
    exec_data = _load_knowledge_file("episodic_memory.json")
    entries = _filter_by_domain(exec_data.get("entries", []), domains)

    corr_data = _load_knowledge_file("corrections.json")
    corrections = _filter_by_domain(corr_data.get("corrections", []), domains)

    refl_data = _load_knowledge_file("reflexion_entries.json")
    reflexions = _filter_by_domain(refl_data.get("entries", []), domains)

    total = len(entries)
    outcomes = Counter(e.get("outcome", "pending_review") for e in entries)
    accepted = outcomes.get("accepted", 0)
    corrected = outcomes.get("corrected", 0)

    total_cost = sum(e.get("cost_usd", 0) for e in entries)
    total_latency = sum(e.get("latency_ms", 0) for e in entries)

    # Per-skill aggregations
    skill_counter: Counter[str] = Counter()
    skill_cost: dict[str, float] = {}
    skill_latency: dict[str, list[float]] = {}
    for e in entries:
        s = e.get("skill", "unknown")
        skill_counter[s] += 1
        skill_cost[s] = skill_cost.get(s, 0) + e.get("cost_usd", 0)
        skill_latency.setdefault(s, []).append(e.get("latency_ms", 0))

    # Correction-to-test rate
    tests_generated = sum(1 for e in entries if e.get("correction_generated_test"))

    # Recent entries (last 10)
    sorted_entries = sorted(entries, key=lambda e: e.get("timestamp", ""), reverse=True)[:10]

    return AnalyticsResponse(
        total_executions=total,
        accepted=accepted,
        corrected=corrected,
        pending_review=outcomes.get("pending_review", 0),
        accept_rate=round(accepted / total, 2) if total else 0,
        total_cost_usd=round(total_cost, 4),
        avg_cost_usd=round(total_cost / total, 4) if total else 0,
        avg_latency_ms=round(total_latency / total, 1) if total else 0,
        total_corrections=len(corrections),
        total_reflexions=len(reflexions),
        correction_to_test_rate=round(tests_generated / len(corrections), 2) if corrections else 0,
        executions_by_skill=dict(skill_counter),
        cost_by_skill={k: round(v, 4) for k, v in skill_cost.items()},
        latency_by_skill={k: round(sum(v) / len(v), 1) for k, v in skill_latency.items()},
        recent_executions=[
            ExecutionEntry(**{k: v for k, v in e.items() if k in ExecutionEntry.model_fields})
            for e in sorted_entries
        ],
    )


# ---------------------------------------------------------------------------
# Knowledge Layer API
# ---------------------------------------------------------------------------


class KnowledgeReflexionEntry(BaseModel):
    reflexion_id: str
    skill: str
    rule: str = ""
    applies_when: str = ""
    confidence: float = 0.0
    validated_by_test: bool = False
    source_correction_id: str = ""
    created_at: str = ""


class KnowledgeCorrectionEntry(BaseModel):
    correction_id: str
    skill: str
    execution_id: str
    original_output: Any = None
    corrected_output: str = ""
    correction_type: str = "domain-specific"
    generated_reflexion_id: str | None = None
    generated_test_ids: list[str] = Field(default_factory=list)
    created_at: str = ""


class TestEntry(BaseModel):
    test_id: str
    skill: str
    test_type: str = "deepeval"
    source: str = "correction"
    description: str = ""
    status: str = "pending"
    source_correction_id: str | None = None


class KnowledgeStats(BaseModel):
    total_corrections: int = 0
    total_reflexions: int = 0
    total_tests: int = 0
    validated_reflexions: int = 0
    learning_rate: float = 0.0
    skills_with_reflexions: int = 0
    skills_with_tests: int = 0


def _scan_generated_tests() -> list[dict]:
    """Scan skills/*/tests/generated/ for test files and build entries."""
    tests: list[dict] = []
    if not SKILLS_DIR.exists():
        return tests

    for domain_dir in SKILLS_DIR.iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith("."):
            continue
        for skill_dir in domain_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith(".") or skill_dir.name in SKIP_DIRS:
                continue
            gen_dir = skill_dir / "tests" / "generated"
            if not gen_dir.exists():
                continue
            skill_name = f"{domain_dir.name}/{skill_dir.name}"
            # Parse corrections.yaml for test entries
            corr_yaml = gen_dir / "corrections.yaml"
            if corr_yaml.exists():
                try:
                    data = yaml.safe_load(corr_yaml.read_text()) or {}
                    for i, t in enumerate(data.get("tests", [])):
                        tests.append({
                            "test_id": f"TEST-{domain_dir.name}-{skill_dir.name}-{i+1}",
                            "skill": skill_name,
                            "test_type": "promptfoo",
                            "source": "correction",
                            "description": t.get("description", t.get("assert", [{}])[0].get("value", ""))[:120],
                            "status": "pending",
                            "source_correction_id": None,
                        })
                except Exception:
                    pass
            # Scan for deepeval test files
            for tf in gen_dir.glob("test_correction_*.py"):
                tests.append({
                    "test_id": f"TEST-{domain_dir.name}-{skill_dir.name}-{tf.stem}",
                    "skill": skill_name,
                    "test_type": "deepeval",
                    "source": "correction",
                    "description": f"DeepEval test from {tf.name}",
                    "status": "pending",
                    "source_correction_id": None,
                })
    return tests


@app.get("/api/v1/knowledge/reflexions", response_model=list[KnowledgeReflexionEntry])
def list_reflexions(skill: str | None = None, domains: set[str] | None = Depends(_get_domain_scope)):
    """List all reflexion entries across all skills (domain-scoped)."""
    # JSON files are source of truth (CLI writes here directly)
    data = _load_knowledge_file("reflexion_entries.json")
    entries = data.get("entries", [])

    entries = _filter_by_domain(entries, domains)
    if skill:
        entries = [e for e in entries if e.get("skill") == skill]

    return [
        KnowledgeReflexionEntry(
            reflexion_id=e.get("reflexion_id", ""),
            skill=e.get("skill", ""),
            rule=e.get("rule", ""),
            applies_when=e.get("applies_when", ""),
            confidence=e.get("confidence", 0.0),
            validated_by_test=e.get("validated_by_test", False),
            source_correction_id=e.get("correction_id", ""),
            created_at=e.get("created_at", ""),
        )
        for e in entries
    ]


@app.get("/api/v1/knowledge/corrections", response_model=list[KnowledgeCorrectionEntry])
def list_corrections(skill: str | None = None, domains: set[str] | None = Depends(_get_domain_scope)):
    """List all corrections across all skills (domain-scoped)."""
    # JSON files are source of truth (CLI writes here directly)
    data = _load_knowledge_file("corrections.json")
    corrections = data.get("corrections", [])
    refl_data = _load_knowledge_file("reflexion_entries.json")
    refl_entries = refl_data.get("entries", [])

    corrections = _filter_by_domain(corrections, domains)
    if skill:
        corrections = [c for c in corrections if c.get("skill") == skill]

    refl_by_corr: dict[str, str] = {}
    for r in refl_entries:
        refl_by_corr[r.get("correction_id", "")] = r.get("reflexion_id", "")

    return [
        KnowledgeCorrectionEntry(
            correction_id=c.get("correction_id", ""),
            skill=c.get("skill", ""),
            execution_id=c.get("execution_id", ""),
            original_output=c.get("original_output"),
            corrected_output=c.get("user_correction", ""),
            correction_type=c.get("correction_type", "domain-specific"),
            generated_reflexion_id=refl_by_corr.get(c.get("correction_id", "")),
            created_at=c.get("timestamp", ""),
        )
        for c in corrections
    ]


@app.get("/api/v1/knowledge/tests", response_model=list[TestEntry])
def list_tests(skill: str | None = None):
    """List generated test cases."""
    tests = _scan_generated_tests()
    if skill:
        tests = [t for t in tests if t.get("skill") == skill]
    return [TestEntry(**t) for t in tests]


@app.get("/api/v1/knowledge/stats", response_model=KnowledgeStats)
def get_knowledge_stats(domains: set[str] | None = Depends(_get_domain_scope)):
    """Learning metrics across all skills (domain-scoped)."""
    corr_data = _load_knowledge_file("corrections.json")
    corrections = _filter_by_domain(corr_data.get("corrections", []), domains)

    refl_data = _load_knowledge_file("reflexion_entries.json")
    reflexions = _filter_by_domain(refl_data.get("entries", []), domains)

    tests = _scan_generated_tests()
    if domains:
        tests = [t for t in tests if t.get("skill", "").split("/")[0] in domains]

    exec_data = _load_knowledge_file("episodic_memory.json")
    entries = _filter_by_domain(exec_data.get("entries", []), domains)

    validated = sum(1 for r in reflexions if r.get("validated_by_test", False))
    skills_with_refl = len({r.get("skill") for r in reflexions})
    skills_with_tests = len({t.get("skill") for t in tests})

    total_execs = len(entries)
    learning_rate = round((len(corrections) / total_execs) * 100, 2) if total_execs else 0.0

    return KnowledgeStats(
        total_corrections=len(corrections),
        total_reflexions=len(reflexions),
        total_tests=len(tests),
        validated_reflexions=validated,
        learning_rate=learning_rate,
        skills_with_reflexions=skills_with_refl,
        skills_with_tests=skills_with_tests,
    )


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 5


class SemanticSearchResult(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list)
    backend: str = "json"  # "mem0" or "json"


@app.post("/api/v1/knowledge/search/{domain}/{skill_name}", response_model=SemanticSearchResult)
def semantic_search(domain: str, skill_name: str, req: SemanticSearchRequest, domains: set[str] | None = Depends(_get_domain_scope)):
    """Semantic search across corrections and reflexions for a skill (domain-scoped)."""
    if domains and domain not in domains:
        raise HTTPException(status_code=403, detail=f"Access denied to domain: {domain}")
    skill_path = f"{domain}/{skill_name}"
    try:
        from agentura_sdk.memory import get_memory_store
        from agentura_sdk.memory.mem0_store import Mem0Store

        store = get_memory_store()
        results = store.search_similar(skill_path, req.query, limit=req.limit)
        backend = "mem0" if isinstance(store, Mem0Store) else "json"
        return SemanticSearchResult(results=results, backend=backend)
    except Exception as e:
        return SemanticSearchResult(results=[], backend=f"error: {e}")


# ---------------------------------------------------------------------------
# Memory Explorer API — Make mem0 visible and interactive
# ---------------------------------------------------------------------------


class MemoryStatus(BaseModel):
    """Memory backend status and statistics."""
    backend: str = "json"  # "mem0" or "json"
    vector_store: str = "none"  # "qdrant-inmemory", "none"
    embedder: str = "none"  # "huggingface/all-MiniLM-L6-v2", "openai"
    llm_provider: str = "none"  # "anthropic", "openai"
    total_memories: int = 0
    execution_memories: int = 0
    correction_memories: int = 0
    reflexion_memories: int = 0
    skills_tracked: list[str] = Field(default_factory=list)


@app.get("/api/v1/memory/status", response_model=MemoryStatus)
def get_memory_status(domains: set[str] | None = Depends(_get_domain_scope)):
    """Memory backend status — is mem0 active, what's stored, what's tracked (domain-scoped)."""
    status = MemoryStatus()

    # Check memory store (Composite, PgStore, Mem0Store, or JSON fallback)
    try:
        from agentura_sdk.memory import get_memory_store
        from agentura_sdk.memory.store import CompositeStore

        store = get_memory_store()

        if isinstance(store, CompositeStore):
            status.backend = "postgresql+mem0"
            status.vector_store = "qdrant-inmemory"
            status.embedder = "huggingface/all-MiniLM-L6-v2"
            if os.environ.get("OPENAI_API_KEY"):
                status.embedder = "openai/text-embedding-ada-002"
            status.llm_provider = "openrouter" if os.environ.get("OPENROUTER_API_KEY") else "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "openai"
        else:
            try:
                from agentura_sdk.memory.pg_store import PgStore
                if isinstance(store, PgStore):
                    status.backend = "postgresql"
            except ImportError:
                pass
            try:
                from agentura_sdk.memory.mem0_store import Mem0Store
                if isinstance(store, Mem0Store):
                    status.backend = "mem0"
                    status.vector_store = "qdrant-inmemory"
                    status.embedder = "huggingface/all-MiniLM-L6-v2"
                    if os.environ.get("OPENAI_API_KEY"):
                        status.embedder = "openai/text-embedding-ada-002"
                    status.llm_provider = "openrouter" if os.environ.get("OPENROUTER_API_KEY") else "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "openai"
            except ImportError:
                pass

        # Count entries
        try:
            status.execution_memories = len(store.get_executions())
        except Exception:
            pass
        try:
            status.correction_memories = len(store.get_corrections())
        except Exception:
            pass
        try:
            status.reflexion_memories = len(store.get_all_reflexions())
        except Exception:
            pass

        status.total_memories = (
            status.execution_memories
            + status.correction_memories
            + status.reflexion_memories
        )
    except Exception:
        pass

    # Also count from JSON files for skills tracked
    exec_data = _load_knowledge_file("episodic_memory.json")
    skills_set: set[str] = set()
    for e in exec_data.get("entries", []):
        s = e.get("skill", "")
        if s:
            skills_set.add(s)
    status.skills_tracked = sorted(skills_set)

    # Count from JSON files — either as primary (json backend) or fallback (mem0 reports 0)
    if status.backend == "json" or status.total_memories == 0:
        json_execs = len(exec_data.get("entries", []))
        corr_data = _load_knowledge_file("corrections.json")
        json_corrs = len(corr_data.get("corrections", []))
        refl_data = _load_knowledge_file("reflexion_entries.json")
        json_refls = len(refl_data.get("entries", []))
        json_total = json_execs + json_corrs + json_refls
        if json_total > status.total_memories:
            status.execution_memories = json_execs
            status.correction_memories = json_corrs
            status.reflexion_memories = json_refls
            status.total_memories = json_total

    return status


class CrossDomainSearchRequest(BaseModel):
    query: str
    limit: int = 10


class MemorySearchResult(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list)
    backend: str = "json"
    query: str = ""
    skills_searched: list[str] = Field(default_factory=list)


@app.post("/api/v1/memory/search", response_model=MemorySearchResult)
def memory_search(req: CrossDomainSearchRequest, domains: set[str] | None = Depends(_get_domain_scope)):
    """Cross-domain semantic search across skill memories (domain-scoped)."""
    exec_data = _load_knowledge_file("episodic_memory.json")
    filtered_entries = _filter_by_domain(exec_data.get("entries", []), domains)
    skills_set: set[str] = set()
    for e in filtered_entries:
        s = e.get("skill", "")
        if s:
            skills_set.add(s)

    all_results: list[dict[str, Any]] = []
    backend = "json"

    try:
        from agentura_sdk.memory import get_memory_store
        from agentura_sdk.memory.mem0_store import Mem0Store

        store = get_memory_store()
        if isinstance(store, Mem0Store):
            backend = "mem0"
            # Search across each skill
            for skill in skills_set:
                hits = store.search_similar(skill, req.query, limit=3)
                for h in hits:
                    h["skill"] = skill
                    all_results.append(h)
    except Exception:
        pass

    # Fallback: word-level text search in JSON entries
    if not all_results:
        backend = "json"
        query_words = [w for w in req.query.lower().split() if len(w) > 2]

        def _word_score(text: str) -> float:
            """Score based on fraction of query words found in text."""
            text_lower = text.lower()
            if not query_words:
                return 0.0
            matches = sum(1 for w in query_words if w in text_lower)
            return matches / len(query_words)

        # Search executions (already domain-filtered)
        for e in filtered_entries:
            text = _json.dumps(e)
            score = _word_score(text) * 0.5
            if score > 0.1:
                all_results.append({
                    "type": "execution",
                    "skill": e.get("skill", ""),
                    "memory": f"Execution of {e.get('skill', '')}: {str(e.get('output_summary', ''))[:200]}",
                    "score": round(score, 2),
                    **{k: v for k, v in e.items() if isinstance(v, (str, int, float, bool))},
                })
        # Search corrections (domain-filtered)
        corr_data = _load_knowledge_file("corrections.json")
        for c in _filter_by_domain(corr_data.get("corrections", []), domains):
            text = _json.dumps(c)
            score = _word_score(text) * 0.85
            if score > 0.1:
                all_results.append({
                    "type": "correction",
                    "skill": c.get("skill", ""),
                    "memory": f"Correction: {c.get('user_correction', '')[:200]}",
                    "score": round(score, 2),
                    **{k: v for k, v in c.items() if isinstance(v, (str, int, float, bool))},
                })
        # Search reflexions (domain-filtered)
        refl_data = _load_knowledge_file("reflexion_entries.json")
        for r in _filter_by_domain(refl_data.get("entries", []), domains):
            text = _json.dumps(r)
            score = _word_score(text) * 0.95
            if score > 0.1:
                all_results.append({
                    "type": "reflexion",
                    "skill": r.get("skill", ""),
                    "memory": f"Rule: {r.get('rule', '')[:200]}",
                    "score": round(score, 2),
                    **{k: v for k, v in r.items() if isinstance(v, (str, int, float, bool))},
                })

    # Sort by score descending, limit
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return MemorySearchResult(
        results=all_results[:req.limit],
        backend=backend,
        query=req.query,
        skills_searched=sorted(skills_set),
    )


class PromptAssemblyResponse(BaseModel):
    """Shows how a skill's system prompt is assembled from 4 layers."""
    skill: str
    workspace_context: str = ""
    domain_context: str = ""
    reflexion_context: str = ""
    skill_prompt: str = ""
    composed_prompt: str = ""
    layers: list[dict[str, str]] = Field(default_factory=list)


@app.get("/api/v1/memory/prompt-assembly/{domain}/{skill_name}", response_model=PromptAssemblyResponse)
def get_prompt_assembly(domain: str, skill_name: str):
    """Show how a skill's system prompt is assembled from WORKSPACE + DOMAIN + reflexions + SKILL."""
    skill_path = SKILLS_DIR / domain / skill_name / "SKILL.md"
    if not skill_path.exists():
        raise HTTPException(status_code=404, detail=f"Skill not found: {domain}/{skill_name}")

    try:
        loaded = load_skill_md(skill_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading skill: {e}")

    layers: list[dict[str, str]] = []
    composed_parts: list[str] = []

    if loaded.workspace_context:
        layers.append({"name": "Workspace Context", "source": "WORKSPACE.md", "content": loaded.workspace_context})
        composed_parts.append(loaded.workspace_context)

    if loaded.domain_context:
        layers.append({"name": "Domain Identity", "source": "DOMAIN.md", "content": loaded.domain_context})
        composed_parts.append(loaded.domain_context)

    if loaded.reflexion_context:
        layers.append({"name": "Reflexion Rules", "source": "mem0 / reflexion_entries.json", "content": loaded.reflexion_context})
        composed_parts.append(loaded.reflexion_context)

    layers.append({"name": "Skill Prompt", "source": "SKILL.md", "content": loaded.system_prompt})
    composed_parts.append(loaded.system_prompt)

    return PromptAssemblyResponse(
        skill=f"{domain}/{skill_name}",
        workspace_context=loaded.workspace_context,
        domain_context=loaded.domain_context,
        reflexion_context=loaded.reflexion_context,
        skill_prompt=loaded.system_prompt,
        composed_prompt="\n\n---\n\n".join(composed_parts),
        layers=layers,
    )


class TestValidationResult(BaseModel):
    skill: str
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    reflexions_validated: list[str] = Field(default_factory=list)


@app.post("/api/v1/knowledge/validate/{domain}/{skill_name}", response_model=TestValidationResult)
def validate_tests(domain: str, skill_name: str):
    """Run generated tests for a skill and update reflexion validation status.

    This closes the loop: Correction → Test → Pass → Reflexion validated.
    """
    import subprocess
    import sys

    skill_path = f"{domain}/{skill_name}"
    skill_dir = SKILLS_DIR / domain / skill_name
    gen_dir = skill_dir / "tests" / "generated"

    if not skill_dir.exists():
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_path}")

    tests_run = 0
    tests_passed = 0
    tests_failed = 0

    # Run DeepEval tests
    for test_file in gen_dir.glob("test_correction_*.py") if gen_dir.exists() else []:
        tests_run += 1
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short", "-q"],
                cwd=str(skill_dir),
                capture_output=True,
                timeout=120,
            )
            if result.returncode == 0:
                tests_passed += 1
            else:
                tests_failed += 1
        except (subprocess.TimeoutExpired, Exception):
            tests_failed += 1

    # Update reflexion entries: mark as validated if tests pass
    reflexions_validated: list[str] = []
    if tests_passed > 0:
        refl_data = _load_knowledge_file("reflexion_entries.json")
        entries = refl_data.get("entries", [])
        updated = False
        for entry in entries:
            if entry.get("skill") == skill_path and not entry.get("validated_by_test"):
                entry["validated_by_test"] = True
                reflexions_validated.append(entry.get("reflexion_id", ""))
                updated = True

        if updated:
            # Write back to reflexion file
            for p in [
                KNOWLEDGE_DIR / "reflexion_entries.json",
                Path.cwd() / ".agentura" / "reflexion_entries.json",
            ]:
                if p.exists():
                    p.write_text(_json.dumps(refl_data, indent=2))
                    break

    return TestValidationResult(
        skill=skill_path,
        tests_run=tests_run,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        reflexions_validated=reflexions_validated,
    )


# ---------------------------------------------------------------------------
# Domain API
# ---------------------------------------------------------------------------


class SkillRoute(BaseModel):
    from_skill: str
    to_skill: str
    route_condition: str = ""


class ResourceQuota(BaseModel):
    """K8s ResourceQuota equivalent — budget/rate enforcement per domain."""
    cost_budget: str = ""
    cost_spent: str = ""
    budget_utilization: float = 0.0  # 0.0-1.0
    max_cost_per_session: str = ""
    max_skills_per_session: int = 0
    rate_limit_rpm: int = 0  # requests per minute
    human_approval_thresholds: list[dict[str, str]] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)


class DomainSummary(BaseModel):
    name: str
    description: str = ""
    owner: str = ""
    skills_count: int = 0
    managers_count: int = 0
    specialists_count: int = 0
    field_agents_count: int = 0
    total_executions: int = 0
    accept_rate: float = 0.0
    total_corrections: int = 0
    total_reflexions: int = 0
    cost_budget: str = ""
    cost_spent: str = ""
    mcp_tools: list[str] = Field(default_factory=list)
    resource_quota: ResourceQuota = Field(default_factory=ResourceQuota)


class DomainDetail(DomainSummary):
    identity: str = ""
    skills: list[SkillInfo] = Field(default_factory=list)
    topology: list[SkillRoute] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    recent_executions: list[ExecutionEntry] = Field(default_factory=list)
    recent_corrections: list[CorrectionEntry] = Field(default_factory=list)


def _build_domain_summary(domain_dir: Path) -> DomainSummary | None:
    """Build a DomainSummary by scanning a domain directory."""
    domain_name = domain_dir.name
    config = _load_domain_config(domain_dir)
    domain_cfg = config.get("domain", {})

    # Read DOMAIN.md for identity
    domain_md = domain_dir / "DOMAIN.md"
    description = domain_cfg.get("description", "")
    if not description and domain_md.exists():
        first_line = domain_md.read_text().strip().split("\n")[0]
        description = first_line.lstrip("# ").strip()

    # Build skill list and count roles
    skill_infos: list[SkillInfo] = []
    managers = specialists = field_agents = 0
    mcp_tools_set: set[str] = set()

    for skill_dir in sorted(domain_dir.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith(".") or skill_dir.name in SKIP_DIRS:
            continue
        info = _build_skill_info(skill_dir, domain_dir)
        if info:
            skill_infos.append(info)
            if info.role == "manager":
                managers += 1
            elif info.role == "specialist":
                specialists += 1
            elif info.role == "field":
                field_agents += 1
            mcp_tools_set.update(info.mcp_tools)

    if not skill_infos:
        return None

    # Execution stats
    exec_data = _load_knowledge_file("episodic_memory.json")
    all_execs = exec_data.get("entries", [])
    domain_execs = [e for e in all_execs if e.get("skill", "").startswith(f"{domain_name}/")]
    accepted = sum(1 for e in domain_execs if e.get("outcome") == "accepted")
    accept_rate = round(accepted / len(domain_execs), 2) if domain_execs else 0.0

    # Corrections + reflexions
    corr_data = _load_knowledge_file("corrections.json")
    domain_corrs = [c for c in corr_data.get("corrections", []) if c.get("skill", "").startswith(f"{domain_name}/")]

    refl_data = _load_knowledge_file("reflexion_entries.json")
    domain_refls = [r for r in refl_data.get("entries", []) if r.get("skill", "").startswith(f"{domain_name}/")]

    # Cost
    total_cost = sum(e.get("cost_usd", 0) for e in domain_execs)

    # Resource quota from guardrails config
    guardrails_cfg = config.get("guardrails", {})
    budget_cfg = guardrails_cfg if isinstance(guardrails_cfg, dict) else {}
    cost_budget_str = config.get("cost_budget", "") or budget_cfg.get("max_cost_per_execution", "")
    max_session = budget_cfg.get("max_cost_per_session", "")
    max_skills = budget_cfg.get("max_skills_per_session", 0)
    rate_cfg = budget_cfg.get("rate_limits", {}) or {}
    rpm = rate_cfg.get("max_executions_per_minute", 0) or rate_cfg.get("requests_per_minute", 0)
    approvals = budget_cfg.get("require_human_approval", []) or []
    blocked = budget_cfg.get("blocked_actions", []) or []

    # Budget utilization
    budget_val = 0.0
    if cost_budget_str:
        try:
            budget_val = float(cost_budget_str.replace("$", "").replace(",", ""))
        except (ValueError, AttributeError):
            pass
    utilization = round(total_cost / budget_val, 2) if budget_val > 0 else 0.0

    quota = ResourceQuota(
        cost_budget=cost_budget_str,
        cost_spent=f"${total_cost:.2f}",
        budget_utilization=min(utilization, 1.0),
        max_cost_per_session=str(max_session) if max_session else "",
        max_skills_per_session=int(max_skills) if max_skills else 0,
        rate_limit_rpm=int(rpm) if rpm else 0,
        human_approval_thresholds=[
            {"action": a.get("action", ""), "threshold": str(a.get("threshold", ""))}
            for a in approvals if isinstance(a, dict)
        ],
        blocked_actions=list(blocked),
    )

    return DomainSummary(
        name=domain_name,
        description=description,
        owner=domain_cfg.get("owner", ""),
        skills_count=len(skill_infos),
        managers_count=managers,
        specialists_count=specialists,
        field_agents_count=field_agents,
        total_executions=len(domain_execs),
        accept_rate=accept_rate,
        total_corrections=len(domain_corrs),
        total_reflexions=len(domain_refls),
        cost_budget=cost_budget_str,
        cost_spent=f"${total_cost:.2f}",
        mcp_tools=sorted(mcp_tools_set),
        resource_quota=quota,
    )


def _build_topology(domain_dir: Path) -> list[SkillRoute]:
    """Parse routes_to from skill metadata to build DAG edges."""
    routes: list[SkillRoute] = []
    domain_name = domain_dir.name

    for skill_dir in domain_dir.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith(".") or skill_dir.name in SKIP_DIRS:
            continue
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            continue
        try:
            loaded = load_skill_md(skill_md_path, include_reflexions=False)
            for rt in loaded.metadata.routes_to:
                target_domain = rt.get("domain", domain_name)
                target_skill = rt.get("skill", "")
                condition = rt.get("when", "")
                if target_domain and not target_skill:
                    target_skill = f"{target_domain}/*"
                routes.append(SkillRoute(
                    from_skill=f"{domain_name}/{skill_dir.name}",
                    to_skill=f"{target_domain}/{target_skill}" if target_skill else target_domain,
                    route_condition=condition,
                ))
        except Exception:
            continue
    return routes


@app.get("/api/v1/domains", response_model=list[DomainSummary])
def list_domains():
    """List all domains with health metrics."""
    domains: list[DomainSummary] = []
    if not SKILLS_DIR.exists():
        return domains

    for domain_dir in sorted(SKILLS_DIR.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("."):
            continue
        summary = _build_domain_summary(domain_dir)
        if summary:
            domains.append(summary)
    return domains


@app.get("/api/v1/domains/{domain}", response_model=DomainDetail)
def get_domain(domain: str):
    """Domain detail with skill topology."""
    domain_dir = SKILLS_DIR / domain
    if not domain_dir.exists() or not domain_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain}")

    summary = _build_domain_summary(domain_dir)
    if not summary:
        raise HTTPException(status_code=404, detail=f"No skills in domain: {domain}")

    # Full identity from DOMAIN.md
    domain_md = domain_dir / "DOMAIN.md"
    identity = domain_md.read_text() if domain_md.exists() else ""

    # Skill list
    skill_infos: list[SkillInfo] = []
    for skill_dir in sorted(domain_dir.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith(".") or skill_dir.name in SKIP_DIRS:
            continue
        info = _build_skill_info(skill_dir, domain_dir)
        if info:
            skill_infos.append(info)

    # Topology
    topology = _build_topology(domain_dir)

    # Guardrails
    guardrails: list[str] = []
    grd_file = domain_dir / "GUARDRAILS.md"
    if grd_file.exists():
        guardrails = [
            line.strip() for line in grd_file.read_text().splitlines()
            if line.strip().startswith("## GRD-")
        ]

    # Recent executions
    exec_data = _load_knowledge_file("episodic_memory.json")
    domain_execs = [
        e for e in exec_data.get("entries", [])
        if e.get("skill", "").startswith(f"{domain}/")
    ]
    domain_execs.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    recent_execs = [
        ExecutionEntry(**{k: v for k, v in e.items() if k in ExecutionEntry.model_fields})
        for e in domain_execs[:10]
    ]

    # Recent corrections
    corr_data = _load_knowledge_file("corrections.json")
    domain_corrs = [
        c for c in corr_data.get("corrections", [])
        if c.get("skill", "").startswith(f"{domain}/")
    ]
    recent_corrs = [
        CorrectionEntry(**{k: v for k, v in c.items() if k in CorrectionEntry.model_fields})
        for c in domain_corrs[:10]
    ]

    return DomainDetail(
        **summary.model_dump(),
        identity=identity,
        skills=skill_infos,
        topology=topology,
        guardrails=guardrails,
        recent_executions=recent_execs,
        recent_corrections=recent_corrs,
    )


# ---------------------------------------------------------------------------
# Events API
# ---------------------------------------------------------------------------


class PlatformEvent(BaseModel):
    event_id: str
    event_type: str  # skill_executed | correction_submitted | reflexion_generated | test_generated | budget_warning
    severity: str = "info"  # info | warning | error
    domain: str = ""
    skill: str = ""
    message: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


@app.get("/api/v1/events", response_model=list[PlatformEvent])
def list_events(domain: str | None = None, event_type: str | None = None, limit: int = 50, domains: set[str] | None = Depends(_get_domain_scope)):
    """Unified event stream across all platform activity (domain-scoped)."""
    events: list[PlatformEvent] = []

    # 1. Executions → skill_executed events
    exec_data = _load_knowledge_file("episodic_memory.json")
    for e in _filter_by_domain(exec_data.get("entries", []), domains):
        skill = e.get("skill", "")
        d = skill.split("/")[0] if "/" in skill else ""
        outcome = e.get("outcome", "pending_review")
        severity = "info" if outcome == "accepted" else "warning" if outcome == "corrected" else "info"
        events.append(PlatformEvent(
            event_id=f"evt-exec-{e.get('execution_id', '')}",
            event_type="skill_executed",
            severity=severity,
            domain=d,
            skill=skill,
            message=f"Skill {skill} executed → {outcome} (${e.get('cost_usd', 0):.2f}, {e.get('latency_ms', 0):.0f}ms)",
            timestamp=e.get("timestamp", ""),
            metadata={"execution_id": e.get("execution_id", ""), "outcome": outcome, "cost_usd": e.get("cost_usd", 0)},
        ))

    # 2. Corrections → correction_submitted events
    corr_data = _load_knowledge_file("corrections.json")
    for c in _filter_by_domain(corr_data.get("corrections", []), domains):
        skill = c.get("skill", "")
        d = skill.split("/")[0] if "/" in skill else ""
        events.append(PlatformEvent(
            event_id=f"evt-corr-{c.get('correction_id', '')}",
            event_type="correction_submitted",
            severity="warning",
            domain=d,
            skill=skill,
            message=f"Correction on {skill}: {c.get('user_correction', '')[:80]}",
            timestamp=c.get("timestamp", ""),
            metadata={"correction_id": c.get("correction_id", ""), "execution_id": c.get("execution_id", "")},
        ))

    # 3. Reflexions → reflexion_generated events
    refl_data = _load_knowledge_file("reflexion_entries.json")
    for r in _filter_by_domain(refl_data.get("entries", []), domains):
        skill = r.get("skill", "")
        d = skill.split("/")[0] if "/" in skill else ""
        events.append(PlatformEvent(
            event_id=f"evt-refl-{r.get('reflexion_id', '')}",
            event_type="reflexion_generated",
            severity="info",
            domain=d,
            skill=skill,
            message=f"Reflexion rule learned for {skill}: {r.get('rule', '')[:80]}",
            timestamp=r.get("created_at", ""),
            metadata={"reflexion_id": r.get("reflexion_id", ""), "confidence": r.get("confidence", 0)},
        ))

    # 4. Tests → test_generated events
    tests = _scan_generated_tests()
    for t in tests:
        skill = t.get("skill", "")
        d = skill.split("/")[0] if "/" in skill else ""
        events.append(PlatformEvent(
            event_id=f"evt-test-{t.get('test_id', '')}",
            event_type="test_generated",
            severity="info",
            domain=d,
            skill=skill,
            message=f"Test generated for {skill}: {t.get('description', '')[:80]}",
            timestamp="",
            metadata={"test_id": t.get("test_id", ""), "test_type": t.get("test_type", "")},
        ))

    # Apply filters
    if domain:
        events = [e for e in events if e.domain == domain]
    if event_type:
        events = [e for e in events if e.event_type == event_type]

    # Sort by timestamp descending, limit
    events.sort(key=lambda e: e.timestamp or "", reverse=True)
    return events[:limit]


# ---------------------------------------------------------------------------
# Platform Health API
# ---------------------------------------------------------------------------


class ComponentHealth(BaseModel):
    name: str
    status: str = "healthy"
    latency_ms: float = 0.0
    version: str = "0.1.0"
    last_check: str = ""


class MCPToolHealth(BaseModel):
    name: str
    status: str = "unknown"
    domains_using: list[str] = Field(default_factory=list)


class PlatformHealth(BaseModel):
    gateway: ComponentHealth
    executor: ComponentHealth
    database: ComponentHealth
    mcp_tools: list[MCPToolHealth] = Field(default_factory=list)


@app.get("/api/v1/platform/health", response_model=PlatformHealth)
def get_platform_health():
    """Component health statuses."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    # Executor is healthy since this code is running on it
    executor_health = ComponentHealth(
        name="executor", status="healthy", latency_ms=0.0, version="0.1.0", last_check=now,
    )

    # Gateway — we can't check from executor, report as unknown unless env hints
    gateway_health = ComponentHealth(
        name="gateway", status="healthy", version="0.1.0", last_check=now,
    )

    # Database — check if knowledge files are accessible
    db_status = "healthy" if (KNOWLEDGE_DIR / "episodic_memory.json").exists() or (Path.cwd() / ".agentura" / "episodic_memory.json").exists() else "no_data"
    database_health = ComponentHealth(
        name="knowledge_store", status=db_status, version="json-fs", last_check=now,
    )

    # MCP tools — scan all domain configs
    mcp_map: dict[str, list[str]] = {}
    if SKILLS_DIR.exists():
        for domain_dir in SKILLS_DIR.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith("."):
                continue
            config = _load_domain_config(domain_dir)
            for tool in config.get("mcp_tools", []):
                server = tool.get("server", "")
                if server:
                    mcp_map.setdefault(server, []).append(domain_dir.name)

    mcp_tools = [
        MCPToolHealth(name=name, status="configured", domains_using=sorted(set(doms)))
        for name, doms in sorted(mcp_map.items())
    ]

    return PlatformHealth(
        gateway=gateway_health,
        executor=executor_health,
        database=database_health,
        mcp_tools=mcp_tools,
    )


# ---------------------------------------------------------------------------
# Skill Creation API — Onboard new agents via UI
# ---------------------------------------------------------------------------


class CreateSkillRequest(BaseModel):
    domain: str = Field(..., pattern=r"^[a-z][a-z0-9-]*$", description="Domain name (lowercase, hyphens ok)")
    name: str = Field(..., pattern=r"^[a-z][a-z0-9-]*$", description="Skill name (lowercase, hyphens ok)")
    role: str = Field(default="specialist", pattern=r"^(manager|specialist|field|agent)$")
    lang: str = Field(default="python", pattern=r"^(python|typescript|go)$")
    description: str = Field(default="", description="One-line description of what the skill does")
    model: str = Field(default="anthropic/claude-sonnet-4-5-20250929")
    trigger: str = Field(default="manual")
    cost_budget: str = Field(default="$0.10")


class CreateSkillResponse(BaseModel):
    domain: str
    name: str
    skill_path: str
    files_created: list[str]
    is_new_domain: bool
    message: str


@app.post("/api/v1/skills", response_model=CreateSkillResponse)
def create_skill(req: CreateSkillRequest):
    """Create a new skill scaffold via the API (same as `agentura create skill`)."""
    from datetime import date

    from jinja2 import Environment, PackageLoader

    domain_root = SKILLS_DIR / req.domain
    skill_root = domain_root / req.name

    if skill_root.exists():
        raise HTTPException(status_code=409, detail=f"Skill already exists: {req.domain}/{req.name}")

    env = Environment(
        loader=PackageLoader("agentura_sdk", "templates"),
        keep_trailing_newline=True,
    )

    context = {
        "domain": req.domain,
        "skill_name": req.name,
        "role": req.role,
        "lang": req.lang,
        "date": date.today().isoformat(),
    }

    # Create directory structure
    dirs = [skill_root, skill_root / "code", skill_root / "tests", skill_root / "fixtures"]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Domain-level files (only if first skill in domain)
    is_new_domain = not (domain_root / "DOMAIN.md").exists()
    domain_files: dict[Path, str] = {}
    if is_new_domain:
        domain_files = {
            domain_root / "DOMAIN.md": "domain.md.j2",
            domain_root / "DECISIONS.md": "decisions.md.j2",
            domain_root / "GUARDRAILS.md": "guardrails.md.j2",
        }

    # Skill-level files
    handler_extensions = {
        "python": ("handler.py", "handler.py.j2"),
        "typescript": ("handler.ts", "handler.ts.j2"),
        "go": ("handler.go", "handler.go.j2"),
    }
    handler_filename, handler_template = handler_extensions[req.lang]

    skill_files: dict[Path, str] = {
        skill_root / "SKILL.md": "skill.md.j2",
        skill_root / "agentura.config.yaml": "agentura.config.yaml.j2",
        skill_root / "tests" / "test_deepeval.py": "test_deepeval.py.j2",
        skill_root / "tests" / "test_promptfoo.yaml": "test_promptfoo.yaml.j2",
        skill_root / "fixtures" / "sample_input.json": "sample_input.json.j2",
        skill_root / "code" / handler_filename: handler_template,
    }

    # Render all files
    all_files = {**domain_files, **skill_files}
    files_created: list[str] = []
    for filepath, template_name in all_files.items():
        template = env.get_template(template_name)
        rendered = template.render(**context)

        # Inject user description into SKILL.md if provided
        if filepath.name == "SKILL.md" and req.description:
            rendered = rendered.replace(
                "[What this skill does in one sentence]",
                req.description,
            )
        # Override model in config
        if filepath.name == "agentura.config.yaml" and req.model:
            rendered = rendered.replace("anthropic/claude-sonnet-4.5", req.model)

        filepath.write_text(rendered)
        files_created.append(str(filepath.relative_to(SKILLS_DIR)))

    return CreateSkillResponse(
        domain=req.domain,
        name=req.name,
        skill_path=f"{req.domain}/{req.name}",
        files_created=files_created,
        is_new_domain=is_new_domain,
        message=f"Skill {req.domain}/{req.name} created successfully"
            + (" (new domain)" if is_new_domain else ""),
    )


# ---------------------------------------------------------------------------
# MCP Registry API — discover and manage MCP tool servers
# ---------------------------------------------------------------------------


class MCPServerInfo(BaseModel):
    name: str
    url: str = ""
    transport: str = "stdio"
    tools: list[str] = Field(default_factory=list)
    description: str = ""
    health: str = "unknown"
    domains_using: list[str] = Field(default_factory=list)


class MCPRegistryResponse(BaseModel):
    servers: list[MCPServerInfo] = Field(default_factory=list)
    total: int = 0


@app.get("/api/v1/mcp/servers", response_model=MCPRegistryResponse)
def list_mcp_servers():
    """List all registered MCP tool servers."""
    from agentura_sdk.mcp import get_registry

    registry = get_registry()
    servers = registry.to_dict()
    return MCPRegistryResponse(
        servers=[MCPServerInfo(**s) for s in servers],
        total=len(servers),
    )


@app.get("/api/v1/mcp/servers/{server_name}", response_model=MCPServerInfo)
def get_mcp_server(server_name: str):
    """Get details for a specific MCP server."""
    from agentura_sdk.mcp import get_registry

    registry = get_registry()
    server = registry.get(server_name)
    if not server:
        raise HTTPException(status_code=404, detail=f"MCP server not found: {server_name}")
    return MCPServerInfo(
        name=server.name,
        url=server.url,
        transport=server.transport,
        tools=server.tools,
        description=server.description,
        health=server.health,
        domains_using=server.domains_using,
    )


@app.post("/api/v1/mcp/servers/{server_name}/health")
def check_mcp_health(server_name: str):
    """Health check a specific MCP server."""
    from agentura_sdk.mcp import get_registry

    registry = get_registry()
    status = registry.health_check(server_name)
    return {"server": server_name, "health": status}


class MCPToolBindingInfo(BaseModel):
    server: str
    tool: str
    health: str = "unknown"


@app.get("/api/v1/mcp/bindings/{domain}/{skill_name}", response_model=list[MCPToolBindingInfo])
def get_skill_mcp_bindings(domain: str, skill_name: str):
    """Get MCP tool bindings for a specific skill."""
    from agentura_sdk.mcp import get_registry

    registry = get_registry()
    bindings = registry.tools_for_skill(f"{domain}/{skill_name}")
    return [
        MCPToolBindingInfo(server=b.server, tool=b.tool, health=b.config.health)
        for b in bindings
    ]


def main():
    """Entry point for agentura-server command."""
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
