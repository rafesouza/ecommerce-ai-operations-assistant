import pytest
def test_inventory_replenishment_recommends_purchase_quantity(client):
    product_response = client.post(
        "/products",
        json={
            "sku": "REPLENISH-001",
            "name": "Test Backpack",
            "price": "79.90",
            "stock_quantity": 30,
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
                    "quantity": 15,
                }
            ]
        },
    )

    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    confirmation = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
    )
    assert confirmation.status_code == 200

    response = client.get(
        "/inventory/replenishment"
        "?days=30&lead_time_days=40&safety_stock=5"
    )

    assert response.status_code == 200

    replenishment = next(
        item
        for item in response.json()
        if item["product_id"] == product_id
    )

    assert replenishment["stock_quantity"] == 15
    assert replenishment["units_sold"] == 15
    assert replenishment["average_daily_sales"] == 0.5
    assert replenishment["lead_time_days"] == 40
    assert replenishment["safety_stock"] == 5
    assert replenishment["recommended_quantity"] == 10

def test_inventory_replenishment_returns_zero_when_stock_is_sufficient(client):
    products = [
        ("REPLENISH-NO-SALES", "Product Without Sales", 50),
        ("REPLENISH-SUFFICIENT", "Product With Sufficient Stock", 25),
    ]

    product_ids = {}

    for sku, name, stock in products:
        response = client.post(
            "/products",
            json={
                "sku": sku,
                "name": name,
                "price": "39.90",
                "stock_quantity": stock,
            },
        )

        assert response.status_code == 201
        product_ids[sku] = response.json()["id"]

    # Sell 5 units of the second product.
    order_response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_ids["REPLENISH-SUFFICIENT"],
                    "quantity": 5,
                }
            ]
        },
    )
    assert order_response.status_code == 201

    confirmation = client.patch(
        f"/orders/{order_response.json()['id']}/status",
        json={"status": "confirmed"},
    )
    assert confirmation.status_code == 200

    response = client.get(
        "/inventory/replenishment"
        "?days=30&lead_time_days=7&safety_stock=5"
    )
    assert response.status_code == 200

    results = {
        item["product_id"]: item
        for item in response.json()
    }

    for product_id in product_ids.values():
        assert results[product_id]["recommended_quantity"] == 0

    assert results[product_ids["REPLENISH-NO-SALES"]]["units_sold"] == 0
    assert results[product_ids["REPLENISH-SUFFICIENT"]]["stock_quantity"] == 20
    assert results[product_ids["REPLENISH-SUFFICIENT"]]["units_sold"] == 5

@pytest.mark.parametrize(
    "query_string",
    [
        "days=0",
        "days=-1",
        "days=366",
        "lead_time_days=0",
        "lead_time_days=-5",
        "lead_time_days=366",
        "safety_stock=-1",
    ],
)
def test_inventory_replenishment_rejects_invalid_parameters(
    client, query_string
):
    response = client.get(
        f"/inventory/replenishment?{query_string}"
    )

    assert response.status_code == 422
