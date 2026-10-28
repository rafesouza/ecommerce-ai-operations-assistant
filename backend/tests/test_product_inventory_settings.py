import pytest
def test_product_can_have_individual_inventory_settings(client):
    response = client.post(
        "/products",
        json={
            "sku": "SETTINGS-001",
            "name": "Premium Backpack",
            "price": "79.90",
            "stock_quantity": 30,
            "lead_time_days": 15,
            "safety_stock": 10,
        },
    )

    assert response.status_code == 201

    product = response.json()

    assert product["lead_time_days"] == 15
    assert product["safety_stock"] == 10

    product_id = product["id"]

    get_response = client.get(f"/products/{product_id}")

    assert get_response.status_code == 200
    assert get_response.json()["lead_time_days"] == 15
    assert get_response.json()["safety_stock"] == 10

def test_product_uses_default_inventory_settings(client):
    response = client.post(
        "/products",
        json={
            "sku": "SETTINGS-DEFAULT-001",
            "name": "Default Settings Product",
            "price": "29.90",
            "stock_quantity": 20,
        },
    )

    assert response.status_code == 201

    product = response.json()

    assert product["lead_time_days"] == 7
    assert product["safety_stock"] == 5

    get_response = client.get(f"/products/{product['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["lead_time_days"] == 7
    assert get_response.json()["safety_stock"] == 5

@pytest.mark.parametrize(
    "settings",
    [
        {"lead_time_days": 0},
        {"lead_time_days": -1},
        {"lead_time_days": 366},
        {"safety_stock": -1},
        {"safety_stock": -10},
    ],
)
def test_product_rejects_invalid_inventory_settings(client, settings):
    product_data = {
        "sku": "SETTINGS-INVALID-001",
        "name": "Invalid Settings Product",
        "price": "29.90",
        "stock_quantity": 20,
    }

    product_data.update(settings)

    response = client.post(
        "/products",
        json=product_data,
    )

    assert response.status_code == 422

def test_replenishment_uses_individual_product_settings(client):
    response = client.post(
        "/products",
        json={
            "sku": "SETTINGS-REPLENISH-001",
            "name": "Custom Replenishment Product",
            "price": "49.90",
            "stock_quantity": 10,
            "lead_time_days": 20,
            "safety_stock": 8,
        },
    )

    assert response.status_code == 201
    product_id = response.json()["id"]

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

    confirmation = client.patch(
        f"/orders/{order_response.json()['id']}/status",
        json={"status": "confirmed"},
    )
    assert confirmation.status_code == 200

    # No global lead time or safety stock parameters.
    replenishment_response = client.get(
        "/inventory/replenishment?days=30"
    )

    assert replenishment_response.status_code == 200

    product_result = next(
        item
        for item in replenishment_response.json()
        if item["product_id"] == product_id
    )

    # 6 units / 30 days = 0.2 units per day.
    # Demand over 20 days = 4 units.
    # Current stock = 4 units.
    # Recommendation = 4 + 8 - 4 = 8 units.
    assert product_result["lead_time_days"] == 20
    assert product_result["safety_stock"] == 8
    assert product_result["recommended_quantity"] == 8

def test_replenishment_url_overrides_product_settings(client):
    response = client.post(
        "/products",
        json={
            "sku": "SETTINGS-OVERRIDE-001",
            "name": "Override Test Product",
            "price": "49.90",
            "stock_quantity": 30,
            "lead_time_days": 20,
            "safety_stock": 8,
        },
    )

    assert response.status_code == 201
    product_id = response.json()["id"]

    order_response = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": product_id, "quantity": 15}
            ]
        },
    )

    assert order_response.status_code == 201

    confirmation = client.patch(
        f"/orders/{order_response.json()['id']}/status",
        json={"status": "confirmed"},
    )
    assert confirmation.status_code == 200

    result = client.get(
        "/inventory/replenishment"
        "?days=30&lead_time_days=40&safety_stock=5"
    )

    assert result.status_code == 200

    product_result = next(
        item for item in result.json()
        if item["product_id"] == product_id
    )

    # Average sales: 15 / 30 = 0.5 per day.
    # Expected demand: 0.5 * 40 = 20.
    # Recommendation: 20 + 5 - 15 = 10.
    assert product_result["lead_time_days"] == 40
    assert product_result["safety_stock"] == 5
    assert product_result["recommended_quantity"] == 10

    # URL overrides must not change saved product settings.
    saved_product = client.get(f"/products/{product_id}")

    assert saved_product.status_code == 200
    assert saved_product.json()["lead_time_days"] == 20
    assert saved_product.json()["safety_stock"] == 8
