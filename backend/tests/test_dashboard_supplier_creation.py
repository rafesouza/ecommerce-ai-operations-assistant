
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_supplier_creation_form_exists():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="supplier-form"' in response.text
    assert 'id="create-supplier-button"' in response.text


def test_supplier_creation_fields_exist():
    response = client.get("/")

    assert response.status_code == 200

    for field in [
        'id="supplier-name"',
        'id="supplier-email"',
        'id="supplier-lead-time"',
    ]:
        assert field in response.text


def test_supplier_creation_javascript_exists():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "async function createSupplier(event)" in response.text
    assert 'method: "POST"' in response.text
    assert 'fetch("/suppliers"' in response.text


def test_supplier_creation_updates_table():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "supplierForm.reset()" in response.text
    assert "await loadSuppliers()" in response.text


def test_supplier_creation_has_feedback():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="supplier-form-message"' in response.text
    assert 'aria-live="polite"' in response.text
