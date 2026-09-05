from health_core.safety import assess_risk, enforce_safety


def test_emergency_language_is_red():
    risk = assess_risk("老人突然说话不清，一边肢体抬不起来")

    assert risk["level"] == "red"
    assert "stroke_sign" in risk["reason_codes"]


def test_medication_change_is_yellow():
    risk = assess_risk("降压药能不能停掉一半？")

    assert risk["level"] == "yellow"
    assert "medication_change" in risk["reason_codes"]


def test_health_education_is_green():
    assert assess_risk("老年人平时怎样预防跌倒？")["level"] == "green"


def test_red_risk_removes_home_treatment_advice():
    unsafe = {"answer": "先在家休息，明天再看看", "attention": ["等待"]}

    safe = enforce_safety(unsafe, assess_risk("胸痛而且呼吸困难"))

    assert "立即" in safe["answer"]
    assert "休息" not in safe["answer"]
    assert safe["attention"] == ["立即联系急救服务或请身边的人协助前往急诊。"]


def test_yellow_risk_removes_positive_medication_commands():
    unsafe = {
        "answer": "建议现在停药并观察",
        "attention": ["把药停掉", "不要自行减量", "记录不舒服的变化"],
    }

    safe = enforce_safety(unsafe, assess_risk("这个药能停吗？"))

    assert "停药" not in safe["answer"]
    assert "把药停掉" not in safe["attention"]
    assert "不要自行减量" in safe["attention"]
