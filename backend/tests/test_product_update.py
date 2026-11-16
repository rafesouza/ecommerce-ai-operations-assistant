
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


@pytest.fixture
def product(client):
    response = client.post(
        "/products",
        json={
            "sku": "UPDATE-001",
            "name": "Original Backpack",
            "price": "49.90",
            "purchase_cost": "25.00",
            "stock_quantity": 10,
            "lead_time_days": 7,
            "safety_stock": 5,
        },
    )

    assert response.status_code == 201
    return response.json()


def test_update_product_price(client, product):
    response = client.patch(
        f"/products/{product['id']}",
        json={"price": "59.90"},
    )

    assert response.status_code == 200
    assert response.json()["price"] == "59.90"
    assert response.json()["name"] == "Original Backpack"


def test_update_product_multiple_fields(client, product):
    response = client.patch(
        f"/products/{product['id']}",
        json={
            "name": "Updated Backpack",
            "purchase_cost": "28.50",
            "lead_time_days": 14,
            "safety_stock": 8,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Backpack"
    assert data["purchase_cost"] == "28.50"
    assert data["lead_time_days"] == 14
    assert data["safety_stock"] == 8


def test_update_product_not_found(client):
    response = client.patch(
        "/products/999999",
        json={"price": "20.00"},
    )

    assert response.status_code == 404


def test_update_product_invalid_price(client, product):
    response = client.patch(
        f"/products/{product['id']}",
        json={"price": "-10.00"},
    )

    assert response.status_code == 422


def test_update_product_null_name(client, product):
    response = client.patch(
        f"/products/{product['id']}",
        json={"name": None},
    )

    assert response.status_code == 422


def test_update_product_clear_purchase_cost(client, product):
    response = client.patch(
        f"/products/{product['id']}",
        json={"purchase_cost": None},
    )

    assert response.status_code == 200
    assert response.json()["purchase_cost"] is None


def test_update_product_invalid_supplier(client, product):
    response = client.patch(
        f"/products/{product['id']}",
        json={"supplier_id": 999999},
    )

    assert response.status_code == 422


def test_update_product_supplier(client, product):
    supplier_response = client.post(
        "/suppliers",
        json={
            "name": "Test Supplier",
            "email": "supplier@example.com",
            "lead_time_days": 7,
        },
    )

    assert supplier_response.status_code == 201
    supplier_id = supplier_response.json()["id"]

    response = client.patch(
        f"/products/{product['id']}",
        json={"supplier_id": supplier_id},
    )

    assert response.status_code == 200
    assert response.json()["supplier_id"] == supplier_id

    clear_response = client.patch(
        f"/products/{product['id']}",
        json={"supplier_id": None},
    )

    assert clear_response.status_code == 200
    assert clear_response.json()["supplier_id"] is None


def test_update_product_preserves_inventory(client, product):
    response = client.patch(
        f"/products/{product['id']}",
        json={"price": "69.90"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sku"] == "UPDATE-001"
    assert data["stock_quantity"] == 10


@pytest.mark.parametrize(
    "field,value",
    [
        ("sku", "CHANGED-SKU"),
        ("stock_quantity", 99),
    ],
)
def test_update_product_rejects_protected_fields(
    client, product, field, value
):
    response = client.patch(
        f"/products/{product['id']}",
        json={field: value},
    )

    assert response.status_code == 422
