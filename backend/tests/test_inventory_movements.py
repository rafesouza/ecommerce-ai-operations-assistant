
from sqlalchemy import select

from backend.app.models import Product


def test_creating_order_records_stock_movement(client):
    product_response = client.post(
        "/products",
        json={
            "sku": "MOVEMENT-001",
            "name": "Test Backpack",
            "price": "79.90",
            "stock_quantity": 10,
        },
    )

    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

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

    with client.testing_session_factory() as session:
        from backend.app.models import StockMovement

        movements = session.scalars(
            select(StockMovement).where(
                StockMovement.product_id == product_id
            )
        ).all()

    assert len(movements) == 1

    movement = movements[0]

    assert movement.order_id == order_id
    assert movement.movement_type == "sale"
    assert movement.quantity == -3

def test_cancelling_order_records_stock_movement(client):
    from backend.app.models import StockMovement

    product_response = client.post(
        "/products",
        json={
            "sku": "MOVEMENT-CANCEL-001",
            "name": "Cancellation Test Backpack",
            "price": "79.90",
            "stock_quantity": 10,
        },
    )

    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

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

    cancel_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "cancelled"},
    )

    assert cancel_response.status_code == 200

    with client.testing_session_factory() as session:
        movements = session.scalars(
            select(StockMovement)
            .where(StockMovement.product_id == product_id)
            .order_by(StockMovement.id)
        ).all()

        movement_data = [
            (m.movement_type, m.quantity, m.order_id)
            for m in movements
        ]

        product = session.get(Product, product_id)
        final_stock = product.stock_quantity

    assert movement_data == [
        ("sale", -3, order_id),
        ("cancellation", 3, order_id),
    ]

    assert final_stock == 10
