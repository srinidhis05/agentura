"""Gateway client — connect CLI to the Agentura API server."""

from __future__ import annotations

import os
from typing import Any

import httpx


def get_gateway_url() -> str:
    """Resolve gateway URL from env or default."""
    return os.environ.get("AGENTURA_GATEWAY_URL", "http://localhost:3001")


def _client() -> httpx.Client:
    """Build a reusable HTTP client with auth if configured."""
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("AGENTURA_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return httpx.Client(base_url=get_gateway_url(), headers=headers, timeout=30.0)


def health_check() -> dict[str, Any]:
    """Check gateway and executor health."""
    with _client() as c:
        try:
            res = c.get("/healthz")
            return {
                "gateway": res.status_code == 200,
                "url": get_gateway_url(),
                "status_code": res.status_code,
            }
        except httpx.ConnectError:
            return {"gateway": False, "url": get_gateway_url(), "error": "Connection refused"}


def list_skills(domain: str | None = None) -> list[dict]:
    """GET /api/v1/skills, optionally filtered by domain."""
    with _client() as c:
        res = c.get("/api/v1/skills")
        res.raise_for_status()
        skills = res.json()
        if domain:
            skills = [s for s in skills if s.get("domain") == domain]
        return skills


def get_skill_detail(domain: str, skill: str) -> dict:
    """GET /api/v1/skills/{domain}/{skill}."""
    with _client() as c:
        res = c.get(f"/api/v1/skills/{domain}/{skill}")
        res.raise_for_status()
        return res.json()


def list_executions(skill: str | None = None) -> list[dict]:
    """GET /api/v1/executions."""
    with _client() as c:
        params = {"skill": skill} if skill else {}
        res = c.get("/api/v1/executions", params=params)
        res.raise_for_status()
        return res.json()


def get_execution(execution_id: str) -> dict:
    """GET /api/v1/executions/{id}."""
    with _client() as c:
        res = c.get(f"/api/v1/executions/{execution_id}")
        res.raise_for_status()
        return res.json()


def execute_skill(domain: str, skill: str, input_data: dict[str, Any], model_override: str | None = None, dry_run: bool = False) -> dict:
    """POST /api/v1/skills/{domain}/{skill}/execute."""
    payload = {"input_data": input_data, "model_override": model_override, "dry_run": dry_run}
    with _client() as c:
        res = c.post(f"/api/v1/skills/{domain}/{skill}/execute", json=payload)
        res.raise_for_status()
        return res.json()


def get_analytics() -> dict:
    """GET /api/v1/analytics."""
    with _client() as c:
        res = c.get("/api/v1/analytics")
        res.raise_for_status()
        return res.json()


def list_events(domain: str | None = None, event_type: str | None = None, limit: int | None = None) -> list[dict]:
    """GET /api/v1/events with optional filters."""
    params = {}
    if domain:
        params["domain"] = domain
    if event_type:
        params["event_type"] = event_type
    if limit:
        params["limit"] = limit
    with _client() as c:
        res = c.get("/api/v1/events", params=params)
        res.raise_for_status()
        return res.json()


def get_memory_status() -> dict:
    """GET /api/v1/memory/status."""
    with _client() as c:
        res = c.get("/api/v1/memory/status")
        res.raise_for_status()
        return res.json()


def memory_search(query: str, limit: int = 10) -> dict:
    """POST /api/v1/memory/search."""
    with _client() as c:
        res = c.post("/api/v1/memory/search", json={"query": query, "limit": limit})
        res.raise_for_status()
        return res.json()


def get_prompt_assembly(domain: str, skill: str) -> dict:
    """GET /api/v1/memory/prompt-assembly/{domain}/{skill}."""
    with _client() as c:
        res = c.get(f"/api/v1/memory/prompt-assembly/{domain}/{skill}")
        res.raise_for_status()
        return res.json()


def approve_execution(execution_id: str, approved: bool, notes: str = "") -> dict:
    """POST /api/v1/executions/{id}/approve."""
    with _client() as c:
        res = c.post(
            f"/api/v1/executions/{execution_id}/approve",
            json={"approved": approved, "reviewer_notes": notes},
        )
        res.raise_for_status()
        return res.json()
