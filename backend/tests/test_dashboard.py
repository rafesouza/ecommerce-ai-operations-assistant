
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_dashboard_returns_html():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "E-commerce AI Operations Assistant" in response.text
    assert 'id="products-table-body"' in response.text


def test_dashboard_css_is_available():
    response = client.get("/static/css/style.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert ".dashboard" in response.text


def test_dashboard_javascript_is_available():
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "loadProducts" in response.text


def test_dashboard_does_not_replace_api_docs():
    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
