from app import (
    build_demo_response,
    is_high_risk_question,
    model_config_status,
    prepare_response,
    validate_question,
)


def test_blank_question_is_rejected():
    assert validate_question("   ") == "请先输入或说出一个健康问题。"


def test_high_risk_question_is_detected():
    assert is_high_risk_question("我能不能把药停了？") is True


def test_demo_response_contains_three_lists():
    result = build_demo_response("高血压平时要注意什么？")
    assert result["answer"]
    assert result["visit_checklist"]
    assert result["doctor_questions"]
    assert result["family_message"]


def test_prepare_response_keeps_required_shape():
    result = prepare_response("感冒发热要注意什么？", mode="demo")
    assert set(result) >= {
        "answer",
        "attention",
        "when_to_seek_care",
        "visit_checklist",
        "doctor_questions",
        "family_message",
        "safety_note",
        "mode",
    }


def test_model_config_status_never_contains_the_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setenv("OPENAI_MODEL", "qwen-plus")
    status = model_config_status()
    assert status["has_api_key"] is True
    assert status["model"] == "qwen-plus"
    assert "test-secret" not in str(status)
