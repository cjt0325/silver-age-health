from health_core.visit_pack import build_visit_pack


def test_visit_pack_uses_only_allowed_fields():
    details = {
        "started": "1—3天",
        "change": "加重",
        "medications": "降压药药盒",
        "conditions": "高血压",
        "name": "张某",
    }

    pack = build_visit_pack("最近头晕", details)

    assert "张某" not in str(pack)
    assert set(pack) == {
        "summary",
        "materials",
        "doctor_questions",
        "family_tasks",
        "privacy_note",
    }


def test_visit_pack_truncates_long_details():
    pack = build_visit_pack("最近头晕", {"medications": "药" * 100})

    assert "药" * 81 not in pack["summary"]
    assert "药" * 80 in pack["summary"]


def test_visit_pack_always_contains_actionable_lists():
    pack = build_visit_pack("准备复诊", {})

    assert len(pack["materials"]) >= 4
    assert len(pack["doctor_questions"]) == 3
    assert len(pack["family_tasks"]) >= 3
    assert "不要填写姓名" in pack["privacy_note"]
