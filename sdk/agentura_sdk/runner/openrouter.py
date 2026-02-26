"""OpenRouter integration — multi-model routing with fallback chains.

Provides a unified interface to 200+ models via OpenRouter's API.
Activated when OPENROUTER_API_KEY is set.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

import httpx

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

MODEL_ALIASES: dict[str, str] = {
    # Short names
    "claude-sonnet-4.5": "anthropic/claude-sonnet-4.5",
    "claude-haiku-4.5": "anthropic/claude-haiku-4.5",
    "claude-opus-4": "anthropic/claude-opus-4",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "gemini-2.0-flash": "google/gemini-2.0-flash-001",
    "deepseek-v3": "deepseek/deepseek-chat",
    "llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct",
    # Dated Anthropic IDs → OpenRouter canonical names
    "anthropic/claude-sonnet-4-5-20250929": "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4-5-20251001": "anthropic/claude-haiku-4.5",
    "anthropic/claude-opus-4-20250514": "anthropic/claude-opus-4",
}

FALLBACK_CHAINS: dict[str, list[str]] = {
    "anthropic/claude-sonnet-4.5": [
        "anthropic/claude-haiku-4.5",
        "openai/gpt-4o-mini",
    ],
    "anthropic/claude-opus-4": [
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-4o",
    ],
    "openai/gpt-4o": [
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-4o-mini",
    ],
}


@dataclass
class ModelResponse:
    content: str
    model: str
    latency_ms: float
    cost_usd: float
    tokens_in: int
    tokens_out: int


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ToolChatResponse:
    content: str | None
    tool_calls: list[ToolCall]
    finish_reason: str  # "stop" or "tool_calls"
    model: str
    tokens_in: int
    tokens_out: int


def _get_client() -> httpx.Client:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return httpx.Client(
        base_url=OPENROUTER_BASE,
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": os.environ.get(
                "OPENROUTER_REFERER", "https://agentura.dev"
            ),
            "X-Title": "Agentura",
            "Content-Type": "application/json",
        },
        timeout=120.0,
    )


def resolve_model(model_name: str) -> str:
    """Resolve aliases to full OpenRouter model IDs."""
    return MODEL_ALIASES.get(model_name, model_name)


def chat_completion(
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    fallback: bool = True,
) -> ModelResponse:
    """Chat completion via OpenRouter with optional fallback chain."""
    resolved = resolve_model(model)
    models_to_try = [resolved]
    if fallback:
        models_to_try.extend(FALLBACK_CHAINS.get(resolved, []))

    last_error: Exception | None = None
    for model_id in models_to_try:
        try:
            return _call_model(
                model_id, system_prompt, user_message, temperature, max_tokens
            )
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All models failed. Last error: {last_error}")


def chat_completion_messages(
    model: str,
    messages: list[dict],
    temperature: float = 0.0,
    max_tokens: int = 4096,
    fallback: bool = True,
) -> ModelResponse:
    """Multi-turn chat completion via OpenRouter."""
    resolved = resolve_model(model)
    models_to_try = [resolved]
    if fallback:
        models_to_try.extend(FALLBACK_CHAINS.get(resolved, []))

    last_error: Exception | None = None
    for model_id in models_to_try:
        try:
            return _call_model_messages(model_id, messages, temperature, max_tokens)
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All models failed. Last error: {last_error}")


def _call_model_messages(
    model_id: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
) -> ModelResponse:
    start = time.monotonic()
    client = _get_client()
    try:
        resp = client.post(
            "/chat/completions",
            json={
                "model": model_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    finally:
        client.close()

    latency_ms = (time.monotonic() - start) * 1000
    choice = data["choices"][0]
    usage = data.get("usage", {})

    return ModelResponse(
        content=choice["message"]["content"],
        model=data.get("model", model_id),
        latency_ms=latency_ms,
        cost_usd=0.0,
        tokens_in=usage.get("prompt_tokens", 0),
        tokens_out=usage.get("completion_tokens", 0),
    )


def _call_model(
    model_id: str,
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_tokens: int,
) -> ModelResponse:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return _call_model_messages(model_id, messages, temperature, max_tokens)


def tool_chat_completion(
    model: str,
    messages: list[dict],
    tools: list[dict],
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> ToolChatResponse:
    """Chat completion with tool calling via OpenRouter."""
    resolved = resolve_model(model)
    client = _get_client()
    try:
        resp = client.post(
            "/chat/completions",
            json={
                "model": resolved,
                "messages": messages,
                "tools": tools,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        body = resp.text.strip()
        if not body:
            raise RuntimeError(f"OpenRouter returned empty body (status {resp.status_code})")
        data = json.loads(body)
    finally:
        client.close()

    choice = data["choices"][0]
    message = choice["message"]
    usage = data.get("usage", {})

    tool_calls = []
    for tc in message.get("tool_calls") or []:
        raw_args = tc["function"]["arguments"]
        if isinstance(raw_args, str) and raw_args.strip():
            args = json.loads(raw_args)
        elif isinstance(raw_args, dict):
            args = raw_args
        else:
            args = {}
        tool_calls.append(ToolCall(
            id=tc["id"],
            name=tc["function"]["name"],
            arguments=args,
        ))

    return ToolChatResponse(
        content=message.get("content"),
        tool_calls=tool_calls,
        finish_reason=choice.get("finish_reason", "stop"),
        model=data.get("model", resolved),
        tokens_in=usage.get("prompt_tokens", 0),
        tokens_out=usage.get("completion_tokens", 0),
    )


def list_models() -> list[dict]:
    """List available models from OpenRouter."""
    client = _get_client()
    try:
        resp = client.get("/models")
        resp.raise_for_status()
        return resp.json().get("data", [])
    finally:
        client.close()
