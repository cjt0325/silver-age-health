import json

import pytest

from health_core import model


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def test_call_chat_model_extracts_fenced_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "qwen3.8-flash")
    payload = {"choices": [{"message": {"content": "```json\n{\"answer\": \"明白\"}\n```"}}]}
    monkeypatch.setattr(model.urlrequest, "urlopen", lambda *_args, **_kwargs: FakeResponse(payload))

    result, elapsed_ms = model.call_chat_model("test prompt")

    assert result == {"answer": "明白"}
    assert elapsed_ms >= 0


def test_model_error_does_not_repeat_the_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-key")

    def fail(*_args, **_kwargs):
        raise RuntimeError("rejected test-secret-key")

    monkeypatch.setattr(model.urlrequest, "urlopen", fail)

    with pytest.raises(model.ModelServiceError) as exc_info:
        model.call_chat_model("test prompt")

    assert "test-secret-key" not in str(exc_info.value)
    assert "[hidden]" in str(exc_info.value)
