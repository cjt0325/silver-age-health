"""银龄健康通：可信健康科普与就医协同演示应用。"""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from health_core.knowledge import retrieve_knowledge
from health_core.model import call_chat_model
from health_core.response import (
    build_prompt,
    get_last_model_error,
    prepare_response as _prepare_response,
    validate_question,
)
from health_core.safety import assess_risk


app = Flask(__name__)


def is_high_risk_question(question: str) -> bool:
    """Compatibility wrapper used by the original test and public module API."""
    return assess_risk(question)["level"] in {"red", "yellow"}


def build_demo_response(question: str) -> dict:
    return _prepare_response(question, mode="demo")


def _prompt(question: str) -> str:
    risk = assess_risk(question)
    matches = [] if risk["level"] == "red" else retrieve_knowledge(question, limit=3)
    return build_prompt(question, matches, risk)


def _call_model(question: str) -> dict:
    result, _elapsed_ms = call_chat_model(_prompt(question))
    return result


def prepare_response(question: str, mode: str | None = None) -> dict:
    return _prepare_response(question, mode=mode)


def model_config_status() -> dict:
    """Return safe local diagnostics without exposing the API key."""
    return {
        "has_api_key": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "base_url": os.getenv(
            "OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ).rstrip("/"),
        "model": os.getenv("OPENAI_MODEL", "qwen3.8-flash"),
        "app_mode": os.getenv("APP_MODE", "auto"),
        "last_error": get_last_model_error(),
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/config-status")
def config_status():
    return jsonify(model_config_status())


@app.post("/api/ask")
def ask():
    body = request.get_json(silent=True) or {}
    question = body.get("question", "")
    error = validate_question(question)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(prepare_response(question, body.get("mode")))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
