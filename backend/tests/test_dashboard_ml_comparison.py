
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_ml_comparison_section_exists():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="ml-model-comparison"' in response.text
    assert 'href="#ml-model-comparison"' in response.text


def test_ml_comparison_controls_exist():
    response = client.get("/")

    assert response.status_code == 200

    for element in [
        'id="ml-comparison-scenario"',
        'id="refresh-ml-comparison-button"',
        'id="ml-comparison-table-body"',
        'id="ml-comparison-status"',
    ]:
        assert element in response.text


def test_ml_comparison_metric_cards_exist():
    response = client.get("/")

    assert response.status_code == 200

    for element in [
        'id="ml-actual-sales"',
        'id="ml-baseline-mae"',
        'id="ml-regression-mae"',
    ]:
        assert element in response.text


def test_ml_comparison_table_exists():
    response = client.get("/")

    assert response.status_code == 200

    for column in [
        "Forecast Method",
        "Predicted Sales",
        "MAE",
        "WAPE",
    ]:
        assert f"<th>{column}</th>" in response.text

    assert 'colspan="4"' in response.text


def test_ml_comparison_scenarios_exist():
    response = client.get("/")

    assert response.status_code == 200

    for scenario in [
        'value="growth"',
        'value="constant"',
        'value="reversal"',
    ]:
        assert scenario in response.text


def test_ml_comparison_javascript_integration():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    assert "function getMLDemoSales(scenario)" in response.text
    assert "function renderMLComparison(data)" in response.text
    assert "async function loadMLComparison()" in response.text
    assert '"/analytics/ml-model-comparison"' in response.text


def test_ml_comparison_uses_post_request():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    assert 'method: "POST"' in response.text
    assert "daily_sales: sales" in response.text
    assert "evaluation_days: 7" in response.text


def test_ml_comparison_handles_all_outcomes():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    assert "mlError < baselineError" in response.text
    assert "baselineError < mlError" in response.text
    assert "Both models achieved the same MAE" in response.text
