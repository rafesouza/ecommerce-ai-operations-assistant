from datetime import datetime, timedelta, timezone

from backend.app.models import Order
def test_inventory_velocity_counts_only_confirmed_orders(client):
    product_response = client.post(
        "/products",
        json={
            "sku": "VELOCITY-001",
            "name": "Test Backpack",
            "price": "79.90",
            "stock_quantity": 30,
        },
    )

    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    def create_order(quantity):
        response = client.post(
            "/orders",
            json={
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": quantity,
                    }
                ]
            },
        )
        assert response.status_code == 201
        return response.json()["id"]

    confirmed_order_id = create_order(6)
    pending_order_id = create_order(4)
    cancelled_order_id = create_order(3)

    confirm_response = client.patch(
        f"/orders/{confirmed_order_id}/status",
        json={"status": "confirmed"},
    )
    assert confirm_response.status_code == 200

    cancel_response = client.patch(
        f"/orders/{cancelled_order_id}/status",
        json={"status": "cancelled"},
    )
    assert cancel_response.status_code == 200

    response = client.get("/inventory/velocity?days=30")

    assert response.status_code == 200

    product_velocity = next(
        item
        for item in response.json()
        if item["product_id"] == product_id
    )

    assert product_velocity["units_sold"] == 6
    assert product_velocity["average_daily_sales"] == 0.2

def test_inventory_velocity_includes_products_without_confirmed_sales(client):
    products = [
        ("VELOCITY-NO-ORDERS", "No Orders", 10),
        ("VELOCITY-PENDING", "Pending Only", 10),
        ("VELOCITY-CANCELLED", "Cancelled Only", 10),
    ]

    product_ids = {}

    for sku, name, stock in products:
        response = client.post(
            "/products",
            json={
                "sku": sku,
                "name": name,
                "price": "29.90",
                "stock_quantity": stock,
            },
        )

        assert response.status_code == 201
        product_ids[sku] = response.json()["id"]

    def create_order(product_id):
        response = client.post(
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
        assert response.status_code == 201
        return response.json()["id"]

    create_order(product_ids["VELOCITY-PENDING"])

    cancelled_order_id = create_order(
        product_ids["VELOCITY-CANCELLED"]
    )

    cancellation = client.patch(
        f"/orders/{cancelled_order_id}/status",
        json={"status": "cancelled"},
    )
    assert cancellation.status_code == 200

    response = client.get("/inventory/velocity?days=30")

    assert response.status_code == 200

    velocity_by_id = {
        item["product_id"]: item
        for item in response.json()
    }

    for product_id in product_ids.values():
        assert product_id in velocity_by_id
        assert velocity_by_id[product_id]["units_sold"] == 0
        assert velocity_by_id[product_id]["average_daily_sales"] == 0

def test_inventory_velocity_excludes_orders_outside_period(client):
    product_response = client.post(
        "/products",
        json={
            "sku": "VELOCITY-DATES-001",
            "name": "Date Filter Backpack",
            "price": "49.90",
            "stock_quantity": 30,
        },
    )

    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    def create_confirmed_order(quantity):
        response = client.post(
            "/orders",
            json={
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": quantity,
                    }
                ]
            },
        )

        assert response.status_code == 201
        order_id = response.json()["id"]

        confirmation = client.patch(
            f"/orders/{order_id}/status",
            json={"status": "confirmed"},
        )
        assert confirmation.status_code == 200

        return order_id

    old_order_id = create_confirmed_order(10)
    create_confirmed_order(6)

    # Simulate an order created 60 days ago.
    with client.testing_session_factory() as session:
        old_order = session.get(Order, old_order_id)
        old_order.created_at = (
            datetime.now(timezone.utc) - timedelta(days=60)
        )
        session.commit()

    response = client.get("/inventory/velocity?days=30")

    assert response.status_code == 200

    product_velocity = next(
        item
        for item in response.json()
        if item["product_id"] == product_id
    )

    assert product_velocity["units_sold"] == 6
    assert product_velocity["average_daily_sales"] == 0.2

import pytest


@pytest.mark.parametrize("days", [0, -5, 366, 500])
def test_inventory_velocity_rejects_invalid_days(client, days):
    response = client.get(
        f"/inventory/velocity?days={days}"
    )

    assert response.status_code == 422
