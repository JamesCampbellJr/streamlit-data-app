"""
Shared AI integration scaffolding for all AI-Company delivery templates.

Design goals (per company standards):
  - Stdlib-only: no hard dependency on openai/langchain. Uses urllib + json.
  - Provider-agnostic: talks to ANY OpenAI-compatible /chat/completions endpoint
    (OpenAI, Anthropic Claude via its proxy, Nous, Mistral, local vLLM, etc).
  - Feature-flagged: set AI_ENABLED=false to run in offline/mock mode (no network,
    no key). Every caller must respect the flag.
  - Safe by default: errors are caught and returned as a structured result, never
    crash the host app.

Env vars (all optional; sane local defaults):
  AI_ENABLED        "true"|"false"  (default: true)
  AI_PROVIDER       label only      (default: "openai-compatible")
  AI_API_KEY        secret          (default: "")
  AI_BASE_URL       endpoint base   (default: "https://api.openai.com/v1")
  AI_MODEL          model name      (default: "gpt-4o-mini")
  AI_TEMPERATURE    float           (default: 0.2)
  AI_MAX_TOKENS     int             (default: 1024)
  AI_TIMEOUT_SECS   int             (default: 30)
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AIResult:
    """Structured outcome of an AI call. Never raises to the caller."""
    ok: bool
    text: str = ""
    error: str = ""
    model: str = ""
    provider: str = ""
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    raw: dict = field(default_factory=dict)


def _env_bool(name: str, default: bool = True) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def ai_enabled() -> bool:
    return _env_bool("AI_ENABLED", default=True)


def chat(
    messages: list[dict],
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout_secs: Optional[int] = None,
) -> AIResult:
    """Send a chat completion. Returns AIResult; never raises.

    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    """
    if not ai_enabled():
        return AIResult(
            ok=False,
            text="",
            error="AI_DISABLED: AI_ENABLED=false. Caller must handle offline path.",
            model=model or os.environ.get("AI_MODEL", ""),
        )

    base = (base_url or os.environ.get("AI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
    key = api_key if api_key is not None else os.environ.get("AI_API_KEY", "")
    model_name = model or os.environ.get("AI_MODEL", "gpt-4o-mini")
    temp = temperature if temperature is not None else float(os.environ.get("AI_TEMPERATURE", "0.2"))
    mtok = max_tokens if max_tokens is not None else int(os.environ.get("AI_MAX_TOKENS", "1024"))
    to = timeout_secs if timeout_secs is not None else int(os.environ.get("AI_TIMEOUT_SECS", "30"))

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temp,
        "max_tokens": mtok,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=to) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        choice = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return AIResult(
            ok=True,
            text=choice,
            model=body.get("model", model_name),
            provider=os.environ.get("AI_PROVIDER", "openai-compatible"),
            tokens_prompt=usage.get("prompt_tokens"),
            tokens_completion=usage.get("completion_tokens"),
            raw=body,
        )
    except urllib.error.HTTPError as e:
        return AIResult(ok=False, error=f"HTTP {e.code}: {e.reason}", model=model_name)
    except urllib.error.URLError as e:
        return AIResult(ok=False, error=f"Network error: {e.reason}", model=model_name)
    except Exception as e:  # noqa: BLE001 - never crash host app
        return AIResult(ok=False, error=f"Unexpected: {type(e).__name__}: {e}", model=model_name)


def complete(prompt: str, *, system: str = "", **kwargs) -> AIResult:
    """Convenience single-prompt helper."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return chat(messages, **kwargs)


if __name__ == "__main__":
    # Smoke test: respects AI_ENABLED flag and reports connectivity.
    os.environ.setdefault("AI_ENABLED", "false")
    r = complete("Say hi in one word.")
    print(json.dumps({"ok": r.ok, "error": r.error, "text": r.text}, indent=2))
