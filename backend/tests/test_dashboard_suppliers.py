
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_dashboard_contains_suppliers_section():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="suppliers"' in response.text
    assert 'id="suppliers-table-body"' in response.text
    assert 'id="refresh-suppliers-button"' in response.text


def test_dashboard_suppliers_navigation():
    response = client.get("/")

    assert response.status_code == 200
    assert 'href="#suppliers"' in response.text


def test_dashboard_javascript_loads_suppliers():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert 'fetch("/suppliers"' in response.text
    assert "async function loadSuppliers()" in response.text
    assert "function renderSuppliers(suppliers)" in response.text


def test_dashboard_suppliers_refresh_button():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert 'refreshSuppliersButton.addEventListener("click"' in response.text
    assert "loadSuppliers" in response.text


def test_dashboard_suppliers_displays_expected_fields():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    for field in [
        "supplier.id",
        "supplier.name",
        "supplier.email",
        "supplier.lead_time_days",
    ]:
        assert field in response.text
