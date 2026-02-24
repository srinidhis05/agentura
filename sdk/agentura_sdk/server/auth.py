"""Auth middleware for the Python executor.

When running behind the Go gateway, the gateway validates JWT tokens and
forwards identity via headers:
  - X-User-ID: authenticated user identifier
  - X-Domain-Scope: comma-separated list of domains the user can access
  - X-Workspace-ID: workspace/org identifier

When AUTH_REQUIRED=true, all /api/v1/ endpoints require these headers.
When AUTH_REQUIRED=false (default for local dev), requests pass through.
"""

from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates gateway-forwarded auth headers on /api/v1/ endpoints."""

    def __init__(self, app, *, required: bool = False):
        super().__init__(app)
        self._required = required

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for health checks and non-API routes
        if path in ("/health", "/healthz", "/readyz") or not path.startswith(
            "/api/v1/"
        ):
            return await call_next(request)

        if not self._required:
            # Dev mode: inject defaults
            request.state.user_id = request.headers.get(
                "x-user-id", "dev-user"
            )
            request.state.domain_scope = request.headers.get(
                "x-domain-scope", "*"
            )
            request.state.workspace_id = request.headers.get(
                "x-workspace-id", "default"
            )
            return await call_next(request)

        # Production: require headers from gateway
        user_id = request.headers.get("x-user-id")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "missing X-User-ID header",
                    "detail": "Request must pass through the gateway",
                },
            )

        domain_scope = request.headers.get("x-domain-scope", "")
        workspace_id = request.headers.get("x-workspace-id", "default")

        # Check domain access for domain-scoped endpoints
        # Pattern: /api/v1/skills/{domain}/... or /api/v1/domains/{domain}
        if domain_scope != "*":
            allowed_domains = {
                d.strip() for d in domain_scope.split(",") if d.strip()
            }
            path_domain = _extract_domain_from_path(path)
            if path_domain and path_domain not in allowed_domains:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "domain access denied",
                        "detail": f"User {user_id} cannot access domain '{path_domain}'",
                        "allowed_domains": sorted(allowed_domains),
                    },
                )

        request.state.user_id = user_id
        request.state.domain_scope = domain_scope
        request.state.workspace_id = workspace_id
        return await call_next(request)


def _extract_domain_from_path(path: str) -> str | None:
    """Extract domain from API paths like /api/v1/skills/{domain}/... or /api/v1/domains/{domain}."""
    parts = path.strip("/").split("/")
    # /api/v1/skills/{domain}/{skill}/...
    if len(parts) >= 4 and parts[2] == "skills":
        return parts[3]
    # /api/v1/domains/{domain}
    if len(parts) >= 4 and parts[2] == "domains":
        return parts[3]
    # /api/v1/knowledge/search/{domain}/{skill}
    if len(parts) >= 5 and parts[2] == "knowledge" and parts[3] == "search":
        return parts[4]
    # /api/v1/knowledge/validate/{domain}/{skill}
    if len(parts) >= 5 and parts[2] == "knowledge" and parts[3] == "validate":
        return parts[4]
    # /api/v1/memory/prompt-assembly/{domain}/{skill}
    if len(parts) >= 5 and parts[2] == "memory" and parts[3] == "prompt-assembly":
        return parts[4]
    return None


def get_auth_required() -> bool:
    """Check if auth is required from environment."""
    return os.environ.get("AUTH_REQUIRED", "").lower() in ("true", "1", "yes")
