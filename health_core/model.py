"""OpenAI-compatible chat adapter used by the Qwen live mode."""

from __future__ import annotations

import json
import os
import re
from time import perf_counter
from urllib import request as urlrequest


class ModelServiceError(RuntimeError):
    """A provider failure whose message is safe to expose locally."""


def _safe_message(exc: Exception, api_key: str) -> str:
    message = str(exc)
    return message.replace(api_key, "[hidden]") if api_key else message


def _extract_json_object(content: object) -> dict:
    if not isinstance(content, str):
        raise ValueError("model content is not text")
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError("model response does not contain JSON")
    result = json.loads(match.group(0))
    if not isinstance(result, dict):
        raise ValueError("model JSON root is not an object")
    return result


def call_chat_model(prompt: str) -> tuple[dict, int]:
    """Call the configured provider and return parsed JSON plus elapsed milliseconds."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ModelServiceError("OPENAI_API_KEY is not configured")
    base_url = os.getenv(
        "OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ).rstrip("/")
    payload = json.dumps(
        {
            "model": os.getenv("OPENAI_MODEL", "qwen3.8-flash"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urlrequest.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = perf_counter()
    try:
        with urlrequest.urlopen(req, timeout=20) as response:
            provider_data = json.loads(response.read().decode("utf-8"))
        content = provider_data["choices"][0]["message"]["content"]
        result = _extract_json_object(content)
    except Exception as exc:
        safe = _safe_message(exc, api_key)
        raise ModelServiceError(f"{type(exc).__name__}: {safe}") from exc
    elapsed_ms = max(0, round((perf_counter() - started) * 1000))
    return result, elapsed_ms
