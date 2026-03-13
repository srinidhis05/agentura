"""OAuth provider registry and DCR discovery for MCP server connections."""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import httpx

_logger = logging.getLogger("agentura.oauth.providers")

PROVIDERS: dict[str, dict] = {
    "granola": {
        "mcp_url": "https://mcp.granola.ai/mcp",
        "resource_metadata": "https://mcp.granola.ai/.well-known/oauth-protected-resource",
        "scopes": "openid email profile offline_access",
        "supports_dcr": True,
    },
    "gmail": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/gmail.modify",
        "supports_dcr": False,
    },
}


def get_provider(name: str) -> dict | None:
    return PROVIDERS.get(name)


def discover_auth_server(provider_name: str) -> dict | None:
    """DCR discovery: fetch resource metadata -> auth server metadata -> return endpoints."""
    provider = PROVIDERS.get(provider_name)
    if not provider or not provider.get("supports_dcr"):
        return None

    resource_url = provider["resource_metadata"]
    try:
        resp = httpx.get(resource_url, timeout=10)
        resp.raise_for_status()
        resource_meta = resp.json()
    except Exception:
        _logger.exception("Failed to fetch resource metadata for %s", provider_name)
        return None

    auth_server_url = resource_meta.get("authorization_servers", [None])[0]
    if not auth_server_url:
        _logger.error("No authorization_servers in resource metadata for %s", provider_name)
        return None

    well_known = auth_server_url.rstrip("/") + "/.well-known/oauth-authorization-server"
    try:
        resp = httpx.get(well_known, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        _logger.exception("Failed to fetch auth server metadata from %s", well_known)
        return None


def register_client(auth_meta: dict, redirect_uri: str) -> dict | None:
    """Dynamic Client Registration (DCR) — registers a new OAuth client."""
    reg_endpoint = auth_meta.get("registration_endpoint")
    if not reg_endpoint:
        _logger.error("No registration_endpoint in auth server metadata")
        return None

    try:
        resp = httpx.post(
            reg_endpoint,
            json={
                "client_name": "Agentura",
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "client_secret_post",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        _logger.exception("DCR registration failed")
        return None


def build_authorize_url(
    provider_name: str,
    user_id: str,
    callback_base: str,
) -> dict:
    """Build the OAuth authorize URL for a provider. Returns {authorize_url, state, client_id, client_secret}."""
    provider = PROVIDERS[provider_name]
    redirect_uri = f"{callback_base.rstrip('/')}/api/v1/oauth/connect/{provider_name}/callback"

    if provider.get("supports_dcr"):
        auth_meta = discover_auth_server(provider_name)
        if not auth_meta:
            raise RuntimeError(f"Failed to discover auth server for {provider_name}")

        client_info = register_client(auth_meta, redirect_uri)
        if not client_info:
            raise RuntimeError(f"DCR registration failed for {provider_name}")

        client_id = client_info["client_id"]
        client_secret = client_info.get("client_secret")
        authorize_url_base = auth_meta["authorization_endpoint"]
        token_url = auth_meta["token_endpoint"]
    else:
        client_id = os.environ.get(f"{provider_name.upper()}_CLIENT_ID", "")
        client_secret = os.environ.get(f"{provider_name.upper()}_CLIENT_SECRET", "")
        if not client_id:
            raise RuntimeError(f"Missing {provider_name.upper()}_CLIENT_ID env var")
        authorize_url_base = provider["authorize_url"]
        token_url = provider["token_url"]

    # Build state: user_id + provider + nonce, signed with HMAC
    import base64
    import hmac
    import json

    state_secret = os.environ.get("OAUTH_STATE_SECRET", "agentura-oauth-default-secret")
    nonce = secrets.token_hex(16)
    state_payload = json.dumps({"user_id": user_id, "provider": provider_name, "nonce": nonce})
    sig = hmac.new(state_secret.encode(), state_payload.encode(), hashlib.sha256).hexdigest()[:16]
    state = base64.urlsafe_b64encode(f"{state_payload}|{sig}".encode()).decode()

    # PKCE code_verifier + code_challenge
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": provider["scopes"],
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if provider_name == "gmail":
        params["access_type"] = "offline"
        params["prompt"] = "consent"

    from urllib.parse import quote
    qs = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())
    authorize_url = f"{authorize_url_base}?{qs}"

    return {
        "authorize_url": authorize_url,
        "state": state,
        "client_id": client_id,
        "client_secret": client_secret,
        "token_url": token_url,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }


def verify_state(state: str) -> dict | None:
    """Verify and decode OAuth state parameter. Returns {user_id, provider, nonce} or None."""
    import base64
    import hmac
    import json

    state_secret = os.environ.get("OAUTH_STATE_SECRET", "agentura-oauth-default-secret")
    try:
        decoded = base64.urlsafe_b64decode(state).decode()
        payload_str, sig = decoded.rsplit("|", 1)
        expected_sig = hmac.new(state_secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected_sig):
            return None
        return json.loads(payload_str)
    except Exception:
        return None


def exchange_code(
    provider_name: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str | None,
    code_verifier: str | None = None,
    token_url: str | None = None,
) -> dict | None:
    """Exchange authorization code for tokens."""
    provider = PROVIDERS[provider_name]
    url = token_url or provider.get("token_url", "")
    if not url:
        auth_meta = discover_auth_server(provider_name)
        if not auth_meta:
            return None
        url = auth_meta["token_endpoint"]

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    }
    if client_secret:
        data["client_secret"] = client_secret
    if code_verifier:
        data["code_verifier"] = code_verifier

    try:
        resp = httpx.post(url, data=data, timeout=10)
        resp.raise_for_status()
        tokens = resp.json()
        result = {
            "access_token": tokens["access_token"],
            "token_type": tokens.get("token_type", "Bearer"),
        }
        if tokens.get("refresh_token"):
            result["refresh_token"] = tokens["refresh_token"]
        if tokens.get("expires_in"):
            result["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=int(tokens["expires_in"]))
        if tokens.get("scope"):
            result["scope"] = tokens["scope"]
        return result
    except Exception:
        _logger.exception("Token exchange failed for %s", provider_name)
        return None


def refresh_access_token(
    provider_name: str,
    refresh_token: str,
    client_id: str | None,
    client_secret: str | None,
) -> dict | None:
    """Refresh an expired access token."""
    provider = PROVIDERS[provider_name]

    if provider.get("supports_dcr"):
        auth_meta = discover_auth_server(provider_name)
        if not auth_meta:
            return None
        token_url = auth_meta["token_endpoint"]
    else:
        token_url = provider.get("token_url", "")

    if not token_url:
        return None

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    if client_id:
        data["client_id"] = client_id
    if client_secret:
        data["client_secret"] = client_secret

    try:
        resp = httpx.post(token_url, data=data, timeout=10)
        resp.raise_for_status()
        tokens = resp.json()
        result = {"access_token": tokens["access_token"]}
        if tokens.get("refresh_token"):
            result["refresh_token"] = tokens["refresh_token"]
        if tokens.get("expires_in"):
            result["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=int(tokens["expires_in"]))
        return result
    except Exception:
        _logger.exception("Token refresh failed for %s", provider_name)
        return None
