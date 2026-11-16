
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import get_db
from backend.app.main import app
from backend.app.models import (
    Base,
    Order,
    OrderItem,
    StockMovement,
)


@pytest.fixture
def client_and_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, TestingSessionLocal
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def product(client_and_session):
    client, _ = client_and_session

    response = client.post(
        "/products",
        json={
            "sku": "DELETE-001",
            "name": "Test Backpack",
            "price": "49.90",
            "purchase_cost": "25.00",
            "stock_quantity": 10,
            "lead_time_days": 7,
            "safety_stock": 5,
        },
    )

    assert response.status_code == 201
    return response.json()


def test_delete_product_success(client_and_session, product):
    client, _ = client_and_session

    response = client.delete(f"/products/{product['id']}")

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get(f"/products/{product['id']}")
    assert get_response.status_code == 404


def test_delete_product_not_found(client_and_session):
    client, _ = client_and_session

    response = client.delete("/products/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_delete_product_with_order(client_and_session, product):
    client, SessionLocal = client_and_session

    with SessionLocal() as db:
        order = Order(status="pending")
        db.add(order)
        db.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=product["id"],
            quantity=1,
            unit_price="49.90",
        )
        db.add(item)
        db.commit()

    response = client.delete(f"/products/{product['id']}")

    assert response.status_code == 409
    assert "orders" in response.json()["detail"].lower()
    assert client.get(f"/products/{product['id']}").status_code == 200


def test_delete_product_with_stock_movement(
    client_and_session,
    product,
):
    client, SessionLocal = client_and_session

    with SessionLocal() as db:
        movement = StockMovement(
            product_id=product["id"],
            movement_type="IN",
            quantity=10,
        )
        db.add(movement)
        db.commit()

    response = client.delete(f"/products/{product['id']}")

    assert response.status_code == 409
    assert "stock movements" in response.json()["detail"].lower()
    assert client.get(f"/products/{product['id']}").status_code == 200


def test_delete_product_removed_from_list(
    client_and_session,
    product,
):
    client, _ = client_and_session

    response = client.delete(f"/products/{product['id']}")
    assert response.status_code == 204

    products_response = client.get("/products")

    assert products_response.status_code == 200
    assert all(
        item["id"] != product["id"]
        for item in products_response.json()
    )
