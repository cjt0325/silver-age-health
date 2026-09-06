"""Validated local health knowledge and explainable retrieval."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE_PATH = BASE_DIR / "data" / "health_knowledge.json"
TRUSTED_HOST = "www.nhc.gov.cn"
REQUIRED_ITEM_FIELDS = {"id", "topic", "keywords", "summary", "attention", "urgent_signs", "source"}
REQUIRED_SOURCE_FIELDS = {"organization", "title", "url", "published_at", "reviewed_at"}


class KnowledgeDataError(ValueError):
    """Raised when local knowledge does not satisfy the trusted schema."""


def _validate_item(item: object, index: int) -> dict:
    if not isinstance(item, dict) or not REQUIRED_ITEM_FIELDS <= item.keys():
        raise KnowledgeDataError(f"knowledge item {index} is missing required fields")
    for field in ("id", "topic", "summary"):
        if not isinstance(item[field], str) or not item[field].strip():
            raise KnowledgeDataError(f"knowledge item {index} has invalid {field}")
    for field in ("keywords", "attention", "urgent_signs"):
        value = item[field]
        if not isinstance(value, list) or not value or not all(isinstance(entry, str) and entry.strip() for entry in value):
            raise KnowledgeDataError(f"knowledge item {index} has invalid {field}")
    source = item["source"]
    if not isinstance(source, dict) or not REQUIRED_SOURCE_FIELDS <= source.keys():
        raise KnowledgeDataError(f"knowledge item {index} has invalid source")
    if urlparse(str(source["url"])).hostname != TRUSTED_HOST:
        raise KnowledgeDataError(f"knowledge item {index} uses an untrusted source")
    return item


def load_knowledge(path: Path | None = None) -> list[dict]:
    """Load and validate the complete local whitelist."""
    source_path = path or DEFAULT_KNOWLEDGE_PATH
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeDataError(f"unable to load knowledge: {exc}") from exc
    if not isinstance(data, list):
        raise KnowledgeDataError("knowledge root must be a list")
    return [_validate_item(item, index) for index, item in enumerate(data)]


def _score(question: str, item: dict) -> int:
    score = sum(2 for keyword in item["keywords"] if len(keyword) >= 2 and keyword in question)
    if item["topic"] in question:
        score += 1
    return score


def retrieve_knowledge(question: str, limit: int = 3) -> list[dict]:
    """Return source-backed matches with transparent lexical scores."""
    text = question.strip() if isinstance(question, str) else ""
    ranked: list[dict] = []
    for item in load_knowledge():
        score = _score(text, item)
        if score:
            match = deepcopy(item)
            match["match_score"] = score
            ranked.append(match)
    ranked.sort(key=lambda item: (-item["match_score"], item["id"]))
    return ranked[: max(0, limit)]


def public_sources(matches: list[dict]) -> list[dict]:
    """Expose deduplicated source cards without internal knowledge text."""
    cards: list[dict] = []
    seen_urls: set[str] = set()
    for item in matches:
        source = item["source"]
        url = source["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        cards.append(
            {
                "id": item["id"],
                "organization": source["organization"],
                "title": source["title"],
                "url": url,
                "published_at": source["published_at"],
            }
        )
    return cards
