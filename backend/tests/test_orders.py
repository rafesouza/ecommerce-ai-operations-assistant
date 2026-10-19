
import pytest

from sqlalchemy import select, func

from backend.app.models import Order, OrderItem
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
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
            test_client.testing_session_factory = TestingSessionLocal
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()

def test_create_order(client):
    # First, create a product in the test database.
    product_response = client.post(
        "/products",
        json={
            "sku": "ORDER-TEST-001",
            "name": "Test Premium Backpack",
            "price": "79.90",
            "stock_quantity": 10,
        },
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    # Create an order with two units of this product.
    order_response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ]
        },
    )

    assert order_response.status_code == 201

    order = order_response.json()

    assert order["id"] > 0
    assert order["status"] == "pending"
    assert order["total"] == "159.80"

    assert len(order["items"]) == 1

    item = order["items"][0]

    assert item["product_id"] == product_id
    assert item["quantity"] == 2
    assert item["unit_price"] == "79.90"
    assert item["subtotal"] == "159.80"

def test_create_order_without_items(client):
    response = client.post(
        "/orders",
        json={
            "items": []
        },
    )

    assert response.status_code == 422

def test_create_order_with_nonexistent_product(client):
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": 99999,
                    "quantity": 2,
                }
            ]
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Product 99999 not found."
    )
    # Confirm that the failed order was not saved.
    with client.testing_session_factory() as session:
        order_count = session.scalar(
            select(func.count()).select_from(Order)
        )

    assert order_count == 0

def test_create_order_with_negative_quantity(client):
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": 1,
                    "quantity": -3,
                }
            ]
        },
    )

    assert response.status_code == 422


def test_create_order_with_duplicate_products(client):
    # Create a valid product in the test database.
    product_response = client.post(
        "/products",
        json={
            "sku": "DUP-ORDER-001",
            "name": "Duplicate Test Backpack",
            "price": "69.90",
            "stock_quantity": 10,
        },
    )

    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    # Attempt to include the same product twice.
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                },
                {
                    "product_id": product_id,
                    "quantity": 1,
                },
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Duplicate products are not allowed."
    )

    # No order should have been saved.
    with client.testing_session_factory() as session:
        order_count = session.scalar(
            select(func.count()).select_from(Order)
        )

    assert order_count == 0

def test_order_items_are_saved(client):
    # Create a product in the temporary test database.
    product_response = client.post(
        "/products",
        json={
            "sku": "PERSIST-001",
            "name": "Premium Backpack",
            "price": "79.90",
            "stock_quantity": 10,
        },
    )

    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    # Create an order with three units.
    order_response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 3,
                }
            ]
        },
    )

    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    # Check the saved data directly in the database.
    with client.testing_session_factory() as session:
        saved_order = session.get(Order, order_id)

        saved_items = session.scalars(
            select(OrderItem).where(
                OrderItem.order_id == order_id
            )
        ).all()

    assert saved_order is not None
    assert saved_order.status == "pending"

    assert len(saved_items) == 1
    assert saved_items[0].product_id == product_id
    assert saved_items[0].quantity == 3
    assert saved_items[0].unit_price == Decimal("79.90")

def test_get_order_by_id(client):
    # Create a product in the temporary database.
    product_response = client.post(
        "/products",
        json={
            "sku": "GET-ORDER-001",
            "name": "Test Backpack",
            "price": "79.90",
            "stock_quantity": 10,
        },
    )

    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    # Create an order with two units.
    order_response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ]
        },
    )

    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    # Retrieve the saved order by its ID.
    response = client.get(f"/orders/{order_id}")

    assert response.status_code == 200

    order = response.json()

    assert order["id"] == order_id
    assert order["status"] == "pending"
    assert order["total"] == "159.80"

    assert len(order["items"]) == 1
    assert order["items"][0]["product_id"] == product_id
    assert order["items"][0]["quantity"] == 2
    assert order["items"][0]["unit_price"] == "79.90"
    assert order["items"][0]["subtotal"] == "159.80"

def test_get_order_not_found(client):
    response = client.get("/orders/99999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Order not found."
    }

def test_list_orders(client):
    # Create a product in the temporary database.
    product_response = client.post(
        "/products",
        json={
            "sku": "LIST-ORDER-001",
            "name": "Test Backpack",
            "price": "79.90",
            "stock_quantity": 10,
        },
    )

    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    # Create an order.
    order_response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ]
        },
    )

    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    # Retrieve all orders.
    response = client.get("/orders")

    assert response.status_code == 200

    orders = response.json()

    assert len(orders) == 1
    assert orders[0]["id"] == order_id
    assert orders[0]["status"] == "pending"
    assert orders[0]["total"] == "159.80"
    assert len(orders[0]["items"]) == 1
    assert orders[0]["items"][0]["product_id"] == product_id
    assert orders[0]["items"][0]["quantity"] == 2
