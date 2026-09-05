from app import app


def test_elder_page_has_risk_sources_and_visit_pack_controls():
    response = app.test_client().get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    for element_id in (
        "risk-banner",
        "source-list",
        "visit-pack-button",
        "visit-pack-form",
        "visit-pack-result",
    ):
        assert f'id="{element_id}"' in html


def test_dashboard_has_metric_and_trace_regions():
    response = app.test_client().get("/evaluation")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="metric-grid"' in html
    assert 'id="system-status"' in html
    assert 'id="category-table"' in html


def test_elder_page_keeps_accessibility_basics():
    html = app.test_client().get("/").get_data(as_text=True)

    assert 'aria-live="assertive"' in html
    assert 'aria-live="polite"' in html
    assert 'for="question"' in html
    assert 'href="/evaluation"' in html


def test_hidden_regions_cannot_be_overridden_by_layout_css():
    css = app.test_client().get("/static/style.css").get_data(as_text=True)

    assert "[hidden]" in css
    assert "display: none !important" in css
