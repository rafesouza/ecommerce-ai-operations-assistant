
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_demand_forecast_section_exists():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="demand-forecast"' in response.text
    assert 'href="#demand-forecast"' in response.text


def test_demand_forecast_controls_exist():
    response = client.get("/")

    assert response.status_code == 200

    for element in [
        'id="forecast-history-period"',
        'id="forecast-horizon"',
        'id="refresh-forecast-button"',
        'id="forecast-table-body"',
    ]:
        assert element in response.text


def test_demand_forecast_table_exists():
    response = client.get("/")

    assert response.status_code == 200

    for column in [
        "Current Stock",
        "Units Sold",
        "Daily Average",
        "Forecast Demand",
        "Stock Gap",
        "Forecast Status",
    ]:
        assert f"<th>{column}</th>" in response.text

    assert 'colspan="8"' in response.text


def test_demand_forecast_javascript_loads_api():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    assert "function renderForecast(products)" in response.text
    assert "async function loadDemandForecast()" in response.text
    assert "/analytics/demand-forecast?history_days=" in response.text
    assert "forecast_days=" in response.text


def test_demand_forecast_handles_missing_history():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    assert "product.forecast_quantity !== null" in response.text
    assert '"Forecast Unavailable"' in response.text
    assert '"Potential Shortage"' in response.text
    assert '"Stock Covers Forecast"' in response.text


def test_demand_forecast_supports_interaction():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    assert "refreshForecastButton.addEventListener(" in response.text
    assert "forecastHistorySelect.addEventListener(" in response.text
    assert "forecastHorizonSelect.addEventListener(" in response.text
    assert "loadDemandForecast" in response.text
