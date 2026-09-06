import json

import pytest

from health_core.knowledge import KnowledgeDataError, load_knowledge, public_sources, retrieve_knowledge


def test_blood_pressure_query_returns_nhc_source():
    matches = retrieve_knowledge("高血压平时要注意什么？")

    assert matches[0]["topic"] == "血压健康管理"
    assert matches[0]["match_score"] > 0
    assert public_sources(matches)[0]["organization"] == "国家卫生健康委员会"


def test_unknown_question_has_no_fake_source():
    assert retrieve_knowledge("量子计算机怎么工作？") == []
    assert public_sources([]) == []


def test_public_source_excludes_internal_content():
    source = public_sources(retrieve_knowledge("老年人怎么防跌倒？"))[0]

    assert set(source) == {"id", "organization", "title", "url", "published_at"}


def test_duplicate_source_is_shown_once():
    sources = public_sources(retrieve_knowledge("高血压和血糖怎么记录？", limit=3))

    assert len({source["url"] for source in sources}) == len(sources)


def test_colloquial_medication_change_still_retrieves_rational_use_source():
    matches = retrieve_knowledge("医生不在时我能自己改药吗？")

    assert matches[0]["topic"] == "老年合理用药"


def test_untrusted_source_is_rejected(tmp_path):
    path = tmp_path / "knowledge.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "bad-source",
                    "topic": "测试",
                    "keywords": ["测试"],
                    "summary": "测试内容",
                    "attention": ["测试"],
                    "urgent_signs": ["测试"],
                    "source": {
                        "organization": "未知机构",
                        "title": "未知资料",
                        "url": "https://example.com/fake",
                        "published_at": "2026-09-06",
                        "reviewed_at": "2026-09-06",
                    },
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgeDataError):
        load_knowledge(path)
