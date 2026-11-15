
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_dashboard_contains_orders_section():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="orders-list"' in response.text
    assert 'id="orders-table-body"' in response.text
    assert 'id="refresh-orders-button"' in response.text


def test_dashboard_orders_navigation():
    response = client.get("/")

    assert response.status_code == 200
    assert 'href="#orders-list"' in response.text


def test_dashboard_javascript_loads_orders():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert 'fetch("/orders"' in response.text
    assert "async function loadOrders()" in response.text
    assert "function renderOrders(orders)" in response.text


def test_dashboard_orders_refresh_button():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert 'refreshOrdersButton.addEventListener("click"' in response.text
    assert "loadOrders();" in response.text
    assert "loadDashboardMetrics();" in response.text


def test_dashboard_orders_displays_expected_fields():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    for field in [
        "order.id",
        "order.created_at",
        "order.status",
        "order.items",
        "order.total",
    ]:
        assert field in response.text
