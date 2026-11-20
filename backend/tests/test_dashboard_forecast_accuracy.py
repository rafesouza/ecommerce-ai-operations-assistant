
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_forecast_accuracy_section_exists():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="forecast-accuracy"' in response.text
    assert 'href="#forecast-accuracy"' in response.text


def test_forecast_accuracy_controls_exist():
    response = client.get("/")

    assert response.status_code == 200

    for element in [
        'id="accuracy-history-period"',
        'id="accuracy-evaluation-period"',
        'id="refresh-accuracy-button"',
        'id="accuracy-table-body"',
    ]:
        assert element in response.text


def test_forecast_accuracy_metrics_exist():
    response = client.get("/")

    assert response.status_code == 200

    for element in [
        'id="accuracy-mae"',
        'id="accuracy-wape"',
        'id="accuracy-evaluated-products"',
    ]:
        assert element in response.text


def test_forecast_accuracy_table_exists():
    response = client.get("/")

    assert response.status_code == 200

    for column in [
        "Historical Sales",
        "Actual Sales",
        "Predicted Sales",
        "Absolute Error",
        "Status",
    ]:
        assert f"<th>{column}</th>" in response.text

    assert 'colspan="7"' in response.text


def test_forecast_accuracy_javascript_integration():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    assert "function renderForecastAccuracy(data)" in response.text
    assert "async function loadForecastAccuracy()" in response.text
    assert "/analytics/forecast-accuracy?history_days=" in response.text
    assert "forecast_days=" in response.text


def test_forecast_accuracy_handles_missing_history():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    assert '"Insufficient History"' in response.text
    assert '"Evaluated"' in response.text
    assert "metrics.wape !== null" in response.text
    assert "refreshAccuracyButton.addEventListener(" in response.text
    assert "accuracyHistorySelect.addEventListener(" in response.text
    assert "accuracyEvaluationSelect.addEventListener(" in response.text
