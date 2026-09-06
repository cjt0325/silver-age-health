"""Deterministic safety routing that always takes priority over model output."""

from __future__ import annotations

from copy import deepcopy
import re


RED_LABEL = "立即求助"
YELLOW_LABEL = "尽快咨询"
GREEN_LABEL = "健康科普"

MEDICATION_TERMS = ("停药", "换药", "改药", "加量", "减量", "药量", "剂量")
NEGATIVE_MARKERS = ("不要", "不能", "不可", "不应", "请勿")
PROMPT_INJECTION_MARKERS = (
    "忽略前面",
    "忽略以上",
    "忽略规则",
    "系统提示词",
    "提示词",
    "绕过安全",
    "越过安全",
    "输出密钥",
    "api key",
)


def is_prompt_injection(text: object) -> bool:
    """Recognize common instructions that try to escape the health-assistant scope."""
    if not isinstance(text, str):
        return False
    normalized = text.strip().lower()
    return any(marker in normalized for marker in PROMPT_INJECTION_MARKERS)


def _mentions_medication_change(text: str) -> bool:
    if any(term in text for term in MEDICATION_TERMS):
        return True
    action = r"(?:停|换|改|加|减)(?:掉|了)?"
    return bool(
        re.search(rf"药.{{0,6}}{action}", text)
        or re.search(rf"{action}.{{0,4}}(?:药|剂量|药量)", text)
    )


def assess_risk(question: str) -> dict[str, object]:
    """Classify a question using explainable red/yellow/green rules."""
    text = question.strip() if isinstance(question, str) else ""
    reasons: list[str] = []

    if any(term in text for term in ("呼吸困难", "意识不清", "昏迷")):
        reasons.append("emergency_sign")
    if "胸痛" in text:
        reasons.append("chest_pain")
    if "说话不清" in text or (
        "肢体" in text and any(term in text for term in ("无力", "抬不起来"))
    ):
        reasons.append("stroke_sign")
    if reasons:
        return {
            "level": "red",
            "label": RED_LABEL,
            "reason_codes": reasons,
            "action": "立即联系急救服务或请身边的人协助前往急诊。",
        }

    if _mentions_medication_change(text):
        reasons.append("medication_change")
    if "诊断" in text:
        reasons.append("diagnosis_request")
    if any(term in text for term in ("持续", "反复", "加重")):
        reasons.append("persistent_or_worsening")
    if reasons:
        return {
            "level": "yellow",
            "label": YELLOW_LABEL,
            "reason_codes": reasons,
            "action": "不要自行作出治疗决定，请尽快咨询医生或药师。",
        }

    return {
        "level": "green",
        "label": GREEN_LABEL,
        "reason_codes": [],
        "action": "可以先了解健康知识，并按需要准备就医资料。",
    }


def _contains_positive_medication_command(text: object) -> bool:
    if not isinstance(text, str) or not _mentions_medication_change(text):
        return False
    return not any(marker in text for marker in NEGATIVE_MARKERS)


def enforce_safety(result: dict, risk: dict) -> dict:
    """Return a copy whose medical-safety fields obey the deterministic route."""
    safe = deepcopy(result) if isinstance(result, dict) else {}
    safe["risk"] = deepcopy(risk)

    if risk.get("level") == "red":
        action = str(risk["action"])
        safe.update(
            {
                "answer": f"这可能是需要紧急处理的情况。{action}",
                "attention": [action],
                "when_to_seek_care": "现在就需要寻求线下紧急医疗帮助，不要等待在线回答。",
                "safety_note": "紧急提示优先：本页面不能代替急救服务。",
            }
        )
        return safe

    if risk.get("level") == "yellow":
        if _contains_positive_medication_command(safe.get("answer")):
            safe["answer"] = "涉及诊断或用药调整时，需要由医生或药师结合实际情况判断。"
        attention = safe.get("attention", [])
        if isinstance(attention, list):
            safe["attention"] = [
                item for item in attention if not _contains_positive_medication_command(item)
            ]
        safe["safety_note"] = str(risk["action"])

    return safe
