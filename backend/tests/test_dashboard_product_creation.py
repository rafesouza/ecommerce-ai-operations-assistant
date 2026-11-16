
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_product_creation_form_exists():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="product-form"' in response.text
    assert 'id="create-product-button"' in response.text


def test_product_creation_fields_exist():
    response = client.get("/")

    assert response.status_code == 200

    for field in [
        'id="product-sku"',
        'id="product-name"',
        'id="product-price"',
        'id="product-purchase-cost"',
        'id="product-stock"',
        'id="product-lead-time"',
        'id="product-safety-stock"',
        'id="product-supplier"',
    ]:
        assert field in response.text


def test_product_creation_javascript_exists():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "async function createProduct(event)" in response.text
    assert 'fetch("/products"' in response.text
    assert 'method: "POST"' in response.text


def test_product_creation_refreshes_dashboard():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "productForm.reset()" in response.text
    assert "await loadProducts()" in response.text
    assert "await loadDashboardMetrics()" in response.text


def test_product_supplier_selection_exists():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "async function loadProductSuppliers()" in response.text
    assert 'fetch("/suppliers"' in response.text
    assert "productSupplierSelect.appendChild(option)" in response.text


def test_product_creation_feedback_exists():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="product-form-message"' in response.text
    assert 'aria-live="polite"' in response.text
