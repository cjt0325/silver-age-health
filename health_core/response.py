"""Safe response orchestration for live and offline modes."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from .knowledge import public_sources, retrieve_knowledge
from .model import call_chat_model
from .safety import assess_risk, enforce_safety, is_prompt_injection


REQUIRED_FIELDS = (
    "answer",
    "attention",
    "when_to_seek_care",
    "visit_checklist",
    "doctor_questions",
    "family_message",
    "safety_note",
)
LIST_FIELDS = {"attention", "visit_checklist", "doctor_questions"}
LAST_MODEL_ERROR: str | None = None


def validate_question(question: object) -> str | None:
    if not isinstance(question, str) or not question.strip():
        return "请先输入或说出一个健康问题。"
    if len(question.strip()) > 200:
        return "问题太长了，请用一句话简单描述。"
    return None


def get_last_model_error() -> str | None:
    return LAST_MODEL_ERROR


def _sanitize_error(exc: Exception) -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    message = str(exc)
    if key:
        message = message.replace(key, "[hidden]")
    return f"{type(exc).__name__}: {message}"


def _base_payload(question: str, matches: list[dict]) -> dict:
    if matches:
        item = matches[0]
        answer = item["summary"]
        attention = list(item["attention"])
        signs = "、".join(item["urgent_signs"])
        when_to_seek_care = f"如果出现{signs}，应及时就医；情况突然或严重时请立即寻求帮助。"
    else:
        answer = "当前资料不足，权威资料库中没有找到足够依据。可以先记录问题、出现时间和变化，再咨询医生或药师。"
        attention = [
            "记录不舒服从什么时候开始以及是否加重。",
            "整理正在使用的药物或药盒。",
            "不要仅凭网络回答自行诊断或调整药物。",
        ]
        when_to_seek_care = "如果不适持续、反复或明显加重，请尽快到正规医疗机构咨询。"
    return {
        "answer": answer,
        "attention": attention,
        "when_to_seek_care": when_to_seek_care,
        "visit_checklist": [
            "症状开始时间和变化记录",
            "正在使用的药物或药盒",
            "既往检查报告",
            "身份证和医保信息",
        ],
        "doctor_questions": [
            "这个情况可能需要做哪些检查？",
            "日常生活中最需要注意什么？",
            "出现什么表现需要尽快复诊？",
        ],
        "family_message": f"家人您好：老人刚刚咨询了“{question}”。请协助记录症状、整理药物和检查资料，必要时陪同就医。",
        "safety_note": "以上内容用于健康教育，不能替代医生诊断；如果症状明显或持续，请及时就医。",
    }


def _scope_payload(question: str) -> dict:
    payload = _base_payload(question, [])
    payload["answer"] = "我只能协助老年健康科普和就医准备。当前问题不在服务范围内。"
    payload["attention"] = ["可以换成症状、慢病管理、用药疑问或就医准备方面的问题。"]
    return payload


def build_prompt(question: str, matches: list[dict], risk: dict) -> str:
    contexts = [
        {
            "id": item["id"],
            "topic": item["topic"],
            "summary": item["summary"],
            "attention": item["attention"],
            "urgent_signs": item["urgent_signs"],
            "match_score": item["match_score"],
        }
        for item in matches
    ]
    return f"""你是面向老年人的健康教育与就医准备助手。你只能依据提供的参考知识回答。
不得诊断疾病，不得判断患病概率，不得建议停药、换药、加量或减量，不得替代医生或急救服务。
如果参考知识为空或不足以支持回答，必须明确说“当前资料不足”，并只提供通用的就医准备建议。
请使用简短、通俗、尊重老人的中文，避免吓人和堆砌术语。
当前风险约束：{json.dumps(risk, ensure_ascii=False)}
用户问题：{question}
参考知识：{json.dumps(contexts, ensure_ascii=False)}
只返回 JSON 对象，字段必须是 answer（字符串）、attention（字符串数组）、when_to_seek_care（字符串）、visit_checklist（字符串数组）、doctor_questions（字符串数组）、family_message（字符串）、safety_note（字符串）。"""


def _normalize(raw: object, fallback: dict) -> dict:
    source = raw if isinstance(raw, dict) else {}
    normalized: dict = {}
    for field in REQUIRED_FIELDS:
        value = source.get(field, fallback[field])
        if field in LIST_FIELDS:
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
                value = fallback[field]
            else:
                value = [item.strip() for item in value]
        elif not isinstance(value, str) or not value.strip():
            value = fallback[field]
        else:
            value = value.strip()
        normalized[field] = deepcopy(value)
    return normalized


def _trace(mode: str, elapsed_ms: int, hits: int, fallback_reason: str | None = None) -> dict:
    trace = {
        "request_id": str(uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": os.getenv("OPENAI_MODEL", "qwen3.8-flash"),
        "mode": mode,
        "elapsed_ms": max(0, int(elapsed_ms)),
        "knowledge_hits": hits,
    }
    if fallback_reason:
        trace["fallback_reason"] = fallback_reason
    return trace


def prepare_response(
    question: str,
    mode: str | None = None,
    model_caller: Callable[[str], tuple[dict, int]] | None = None,
) -> dict:
    """Create one complete response with sources, safety and a public trace."""
    global LAST_MODEL_ERROR
    error = validate_question(question)
    if error:
        raise ValueError(error)
    clean_question = question.strip()
    risk = assess_risk(clean_question)
    injection_attempt = is_prompt_injection(clean_question)
    matches = [] if risk["level"] == "red" or injection_attempt else retrieve_knowledge(clean_question, limit=3)
    scope_blocked = risk["level"] != "red" and (injection_attempt or not matches)
    fallback = _scope_payload(clean_question) if scope_blocked else _base_payload(clean_question, matches)
    requested_mode = mode or os.getenv("APP_MODE", "auto")
    configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
    should_call = not scope_blocked and risk["level"] != "red" and (
        requested_mode == "live" or (requested_mode == "auto" and (configured or model_caller is not None))
    )
    elapsed_ms = 0
    fallback_reason: str | None = None

    if should_call:
        try:
            raw, elapsed_ms = (model_caller or call_chat_model)(build_prompt(clean_question, matches, risk))
            payload = _normalize(raw, fallback)
            response_mode = "live"
            LAST_MODEL_ERROR = None
        except Exception as exc:
            LAST_MODEL_ERROR = _sanitize_error(exc)
            payload = deepcopy(fallback)
            payload["safety_note"] += " 当前模型服务不可用，页面展示的是本地安全内容。"
            response_mode = "demo"
            fallback_reason = "model_unavailable"
    else:
        payload = deepcopy(fallback)
        response_mode = "safety" if risk["level"] == "red" else "scope" if scope_blocked else "demo"

    result = enforce_safety(payload, risk)
    result["sources"] = public_sources(matches)
    result["trace"] = _trace(response_mode, elapsed_ms, len(matches), fallback_reason)
    result["follow_up_available"] = risk["level"] != "red" and bool(matches)
    result["mode"] = response_mode
    return result
