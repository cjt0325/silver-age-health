"""Stateless consultation preparation for older adults and their families."""

from __future__ import annotations


ALLOWED_DETAIL_FIELDS = ("started", "change", "medications", "conditions")
DETAIL_LABELS = {
    "started": "开始时间",
    "change": "变化情况",
    "medications": "正在使用的药物或药盒",
    "conditions": "已有基础疾病",
}
PRIVACY_NOTE = "本准备包只在当前页面使用，请不要填写姓名、身份证号或病历号。"


def _clean_details(details: object) -> dict[str, str]:
    if not isinstance(details, dict):
        return {}
    cleaned: dict[str, str] = {}
    for field in ALLOWED_DETAIL_FIELDS:
        value = details.get(field)
        if isinstance(value, str) and value.strip():
            cleaned[field] = value.strip()[:80]
    return cleaned


def build_visit_pack(question: str, details: dict[str, str]) -> dict:
    """Build an actionable package without storing or returning extra fields."""
    clean_question = question.strip()[:200]
    cleaned = _clean_details(details)
    parts = [f"需要向医生说明的问题：{clean_question}。"]
    parts.extend(f"{DETAIL_LABELS[field]}：{value}。" for field, value in cleaned.items())
    if not cleaned:
        parts.append("目前尚未补充开始时间、变化、用药和基础疾病信息。")
    return {
        "summary": "".join(parts),
        "materials": [
            "身份证和医保信息",
            "既往检查报告",
            "正在使用的药物或药盒",
            "症状开始时间与变化记录",
        ],
        "doctor_questions": [
            "根据目前情况，需要做哪些检查？",
            "现有药物需要注意哪些不良反应或相互影响？",
            "出现哪些表现需要尽快复诊或急诊？",
        ],
        "family_tasks": [
            "帮助老人把症状开始时间和变化写下来。",
            "核对药盒、检查报告和医保信息是否带齐。",
            "就诊时帮助记录医生交代的事项，必要时陪同。",
        ],
        "privacy_note": PRIVACY_NOTE,
    }
