"""银龄健康通：健康科普与就医协同演示应用。"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib import request as urlrequest

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_PATH = BASE_DIR / "data" / "health_knowledge.json"
REQUIRED_FIELDS = (
    "answer",
    "attention",
    "when_to_seek_care",
    "visit_checklist",
    "doctor_questions",
    "family_message",
    "safety_note",
)
HIGH_RISK_TERMS = (
    "诊断",
    "改药",
    "停药",
    "药停",
    "药量",
    "急救",
    "胸痛",
    "呼吸困难",
    "意识不清",
    "不去医院",
)

app = Flask(__name__)
LAST_MODEL_ERROR = None


def validate_question(question: str) -> str | None:
    """Return a user-facing error for invalid input, otherwise None."""
    if not isinstance(question, str) or not question.strip():
        return "请先输入或说出一个健康问题。"
    if len(question.strip()) > 200:
        return "问题太长了，请用一句话简单描述。"
    return None


def is_high_risk_question(question: str) -> bool:
    return any(term in question for term in HIGH_RISK_TERMS)


def _load_knowledge() -> list[dict]:
    try:
        return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _find_topic(question: str) -> dict:
    for item in _load_knowledge():
        if any(keyword in question for keyword in item.get("keywords", [])):
            return item
    return {
        "answer": "健康问题需要结合年龄、既往病史和检查结果判断。先把不舒服的部位、持续时间和变化记下来，再向医生说明。",
        "attention": [
            "记录症状从什么时候开始，以及是变重还是变轻。",
            "把正在服用的药物名称或药盒拍照带给医生。",
            "不要因为一次不舒服就自行停药或加药。",
        ],
        "when_to_seek_care": "如果症状持续、反复或明显加重，建议尽快到正规医疗机构咨询。",
        "visit_checklist": ["身份证和医保信息", "既往检查报告", "正在服用的药物或药盒", "症状出现时间和变化记录"],
        "doctor_questions": ["这个症状可能需要做哪些检查？", "日常生活中最需要注意什么？", "出现什么情况需要尽快复诊？"],
    }


def _safety_note(question: str) -> str:
    if any(term in question for term in ("胸痛", "呼吸困难", "意识不清", "急救")):
        return "这类情况可能需要及时处理。请立即联系急救服务或前往急诊，不要只依赖在线回答。"
    if is_high_risk_question(question):
        return "我不能替你诊断、改药或决定是否停药。涉及治疗决定时，请把问题和药物信息交给医生或药师确认。"
    return "以上内容用于健康教育，不能替代医生诊断；如果症状明显或持续，请及时就医。"


def build_demo_response(question: str) -> dict:
    topic = _find_topic(question)
    return {
        "answer": topic["answer"],
        "attention": list(topic["attention"]),
        "when_to_seek_care": topic["when_to_seek_care"],
        "visit_checklist": list(topic["visit_checklist"]),
        "doctor_questions": list(topic["doctor_questions"]),
        "family_message": f"家人您好：老人刚刚咨询了“{question.strip()}”。建议陪同记录症状，并准备好相关资料，必要时陪同就医。",
        "safety_note": _safety_note(question),
        "mode": "demo",
    }


def _prompt(question: str) -> str:
    context = json.dumps(_find_topic(question), ensure_ascii=False)
    return f"""你是老年健康教育助手，只能做健康科普和就医准备，不能诊断、改药或替代医生。
请用老人听得懂的中文回答问题：{question}
参考知识：{context}
只返回 JSON，字段必须是 answer（字符串）、attention（字符串数组）、when_to_seek_care（字符串）、visit_checklist（字符串数组）、doctor_questions（字符串数组）、family_message（字符串）、safety_note（字符串）。"""


def _call_model(question: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = json.dumps(
        {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": _prompt(question)}],
            "temperature": 0.2,
        }
    ).encode("utf-8")
    req = urlrequest.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError("model response is not JSON")
    result = json.loads(match.group(0))
    result["mode"] = "live"
    return result


def model_config_status() -> dict:
    """Return safe local diagnostics without exposing the API key."""
    return {
        "has_api_key": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "app_mode": os.getenv("APP_MODE", "auto"),
        "last_error": LAST_MODEL_ERROR,
    }


def _normalize_response(result: dict, question: str, mode: str) -> dict:
    fallback = build_demo_response(question)
    normalized = {}
    for field in REQUIRED_FIELDS:
        value = result.get(field, fallback[field])
        if field in {"attention", "visit_checklist", "doctor_questions"}:
            value = value if isinstance(value, list) and value else fallback[field]
        elif not isinstance(value, str) or not value.strip():
            value = fallback[field]
        normalized[field] = value
    normalized["mode"] = mode
    if is_high_risk_question(question):
        normalized["safety_note"] = _safety_note(question)
    return normalized


def prepare_response(question: str, mode: str | None = None) -> dict:
    global LAST_MODEL_ERROR
    error = validate_question(question)
    if error:
        raise ValueError(error)
    clean_question = question.strip()
    requested_mode = mode or os.getenv("APP_MODE", "auto")
    if requested_mode == "demo" or (requested_mode == "auto" and not os.getenv("OPENAI_API_KEY", "").strip()):
        return build_demo_response(clean_question)
    try:
        response = _normalize_response(_call_model(clean_question), clean_question, "live")
        LAST_MODEL_ERROR = None
        return response
    except Exception as exc:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        safe_error = str(exc)
        if api_key:
            safe_error = safe_error.replace(api_key, "[hidden]")
        LAST_MODEL_ERROR = f"{type(exc).__name__}: {safe_error}"
        fallback = build_demo_response(clean_question)
        fallback["safety_note"] += " 当前模型服务不可用，页面展示的是演示内容。"
        return fallback


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
