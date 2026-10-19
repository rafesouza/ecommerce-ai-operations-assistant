
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import get_db
from backend.app.main import app
from backend.app.models import Base


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def test_create_product(client):
    response = client.post(
        "/products",
        json={
            "sku": "TEST-001",
            "name": "Test Backpack",
            "price": "49.90",
            "stock_quantity": 10,
        },
    )

    assert response.status_code == 201
    assert response.json()["sku"] == "TEST-001"
    assert response.json()["price"] == "49.90"
    assert response.json()["stock_quantity"] == 10


def test_create_product_with_negative_price(client):
    response = client.post(
        "/products",
        json={
            "sku": "TEST-002",
            "name": "Invalid Backpack",
            "price": "-10.00",
            "stock_quantity": 5,
        },
    )

    assert response.status_code == 422

def test_create_product_with_duplicate_sku(client):
    product_data = {
        "sku": "DUPLICATE-001",
        "name": "Test Backpack",
        "price": "49.90",
        "stock_quantity": 10,
    }

    # First registration should succeed
    first_response = client.post(
        "/products",
        json=product_data,
    )

    assert first_response.status_code == 201

    # Registering the same SKU again should fail
    second_response = client.post(
        "/products",
        json=product_data,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A product with this SKU already exists."
    )

def test_create_product_with_negative_stock(client):
    response = client.post(
        "/products",
        json={
            "sku": "TEST-NEGATIVE-STOCK",
            "name": "Invalid Stock Backpack",
            "price": "59.90",
            "stock_quantity": -5,
        },
    )

    assert response.status_code == 422

def test_list_products(client):
    # Create a product in the temporary test database
    product_data = {
        "sku": "LIST-001",
        "name": "List Test Backpack",
        "price": "89.90",
        "stock_quantity": 20,
    }

    create_response = client.post(
        "/products",
        json=product_data,
    )

    assert create_response.status_code == 201

    # Request all products
    response = client.get("/products")

    assert response.status_code == 200

    products = response.json()

    assert len(products) == 1
    assert products[0]["sku"] == "LIST-001"
    assert products[0]["name"] == "List Test Backpack"
    assert products[0]["price"] == "89.90"
    assert products[0]["stock_quantity"] == 20

def test_get_product_by_id(client):
    # Create a product in the temporary database
    create_response = client.post(
        "/products",
        json={
            "sku": "DETAIL-001",
            "name": "Premium Backpack",
            "price": "109.90",
            "stock_quantity": 8,
        },
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    # Retrieve the product using its ID
    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200

    product = response.json()

    assert product["id"] == product_id
    assert product["sku"] == "DETAIL-001"
    assert product["name"] == "Premium Backpack"
    assert product["price"] == "109.90"
    assert product["stock_quantity"] == 8

def test_get_product_not_found(client):
    response = client.get("/products/99999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product not found."
    }
