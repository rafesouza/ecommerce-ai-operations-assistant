
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_dashboard_contains_metric_elements():
    response = client.get("/")

    assert response.status_code == 200

    for metric_id in [
        "total-products",
        "total-orders",
        "low-stock-products",
        "confirmed-revenue",
    ]:
        assert f'id="{metric_id}"' in response.text


def test_dashboard_javascript_loads_analytics():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert 'fetch("/analytics/summary"' in response.text
    assert "loadDashboardMetrics" in response.text


def test_dashboard_javascript_reads_analytics_fields():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    for field in [
        "total_orders",
        "low_stock_products",
        "confirmed_revenue",
    ]:
        assert field in response.text


def test_dashboard_refresh_updates_metrics():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert 'refreshButton.addEventListener("click"' in response.text
    assert "loadProducts();" in response.text
    assert "loadDashboardMetrics();" in response.text
