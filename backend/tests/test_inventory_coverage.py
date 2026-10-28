import pytest
def test_inventory_coverage_calculates_days_remaining(client):
    product_response = client.post(
        "/products",
        json={
            "sku": "COVERAGE-001",
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
                    "quantity": 6,
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

    response = client.get("/inventory/coverage?days=30")

    assert response.status_code == 200

    product_coverage = next(
        item
        for item in response.json()
        if item["product_id"] == product_id
    )

    assert product_coverage["stock_quantity"] == 24
    assert product_coverage["units_sold"] == 6
    assert product_coverage["average_daily_sales"] == 0.2
    assert product_coverage["days_remaining"] == 120.0

def test_inventory_coverage_handles_zero_sales_and_zero_stock(client):
    # Product with stock but no sales.
    no_sales_response = client.post(
        "/products",
        json={
            "sku": "COVERAGE-NO-SALES",
            "name": "Product Without Sales",
            "price": "29.90",
            "stock_quantity": 10,
        },
    )
    assert no_sales_response.status_code == 201
    no_sales_id = no_sales_response.json()["id"]

    # Product without stock or sales.
    empty_response = client.post(
        "/products",
        json={
            "sku": "COVERAGE-EMPTY",
            "name": "Empty Product",
            "price": "29.90",
            "stock_quantity": 0,
        },
    )
    assert empty_response.status_code == 201
    empty_id = empty_response.json()["id"]

    # Product whose entire stock will be sold.
    sold_out_response = client.post(
        "/products",
        json={
            "sku": "COVERAGE-SOLD-OUT",
            "name": "Sold Out Product",
            "price": "29.90",
            "stock_quantity": 5,
        },
    )
    assert sold_out_response.status_code == 201
    sold_out_id = sold_out_response.json()["id"]

    order_response = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": sold_out_id, "quantity": 5}
            ]
        },
    )
    assert order_response.status_code == 201

    confirmation = client.patch(
        f"/orders/{order_response.json()['id']}/status",
        json={"status": "confirmed"},
    )
    assert confirmation.status_code == 200

    response = client.get("/inventory/coverage?days=30")
    assert response.status_code == 200

    results = {
        item["product_id"]: item
        for item in response.json()
    }

    assert results[no_sales_id]["units_sold"] == 0
    assert results[no_sales_id]["days_remaining"] is None

    assert results[empty_id]["stock_quantity"] == 0
    assert results[empty_id]["days_remaining"] is None

    assert results[sold_out_id]["stock_quantity"] == 0
    assert results[sold_out_id]["units_sold"] == 5
    assert results[sold_out_id]["days_remaining"] == 0.0

@pytest.mark.parametrize("days", [0, -1, 366, 500])
def test_inventory_coverage_rejects_invalid_days(client, days):
    response = client.get(
        f"/inventory/coverage?days={days}"
    )

    assert response.status_code == 422
