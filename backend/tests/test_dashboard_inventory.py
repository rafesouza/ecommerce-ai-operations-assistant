
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_inventory_section_exists():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="inventory-intelligence"' in response.text
    assert 'href="#inventory-intelligence"' in response.text


def test_inventory_controls_exist():
    response = client.get("/")

    assert response.status_code == 200

    for element in [
        'id="inventory-period"',
        'id="refresh-inventory-button"',
        'id="inventory-table-body"',
    ]:
        assert element in response.text


def test_inventory_period_options_exist():
    response = client.get("/")

    assert response.status_code == 200

    for period in [7, 30, 60, 90]:
        assert f'value="{period}"' in response.text


def test_inventory_table_columns_exist():
    response = client.get("/")

    assert response.status_code == 200

    for column in [
        "SKU",
        "Product",
        "Stock",
        "Units Sold",
        "Daily Sales",
        "Lead Time",
        "Safety Stock",
        "Reorder Qty",
        "Status",
    ]:
        assert f"<th>{column}</th>" in response.text

    assert 'colspan="9"' in response.text


def test_inventory_javascript_loads_replenishment():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "function renderInventory(products)" in response.text
    assert "async function loadInventory()" in response.text
    assert "/inventory/replenishment?days=" in response.text


def test_inventory_javascript_handles_status():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200

    for status in [
        "Out of Stock",
        "Reorder Needed",
        "No Reorder Needed",
    ]:
        assert status in response.text

    assert "cell.colSpan = 9" in response.text


def test_inventory_status_styles_exist():
    response = client.get("/static/css/style.css")

    assert response.status_code == 200

    for style in [
        ".inventory-status",
        ".inventory-status.out-of-stock",
        ".inventory-status.reorder-needed",
        ".inventory-status.no-reorder",
    ]:
        assert style in response.text
