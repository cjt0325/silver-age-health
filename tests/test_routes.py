from app import app


def test_visit_pack_route_rejects_blank_question():
    client = app.test_client()

    response = client.post("/api/visit-pack", json={"question": " ", "details": {}})

    assert response.status_code == 400


def test_visit_pack_route_rejects_non_object_details():
    client = app.test_client()

    response = client.post("/api/visit-pack", json={"question": "最近头晕", "details": []})

    assert response.status_code == 400


def test_visit_pack_route_returns_private_pack():
    client = app.test_client()

    response = client.post(
        "/api/visit-pack",
        json={"question": "最近头晕", "details": {"started": "今天", "name": "不应保存"}},
    )

    assert response.status_code == 200
    assert "不应保存" not in str(response.json)


def test_ask_route_returns_new_contract():
    client = app.test_client()

    response = client.post(
        "/api/ask", json={"question": "老年人怎么防跌倒？", "mode": "demo"}
    )

    assert response.status_code == 200
    assert {"risk", "sources", "trace", "follow_up_available"} <= response.json.keys()
