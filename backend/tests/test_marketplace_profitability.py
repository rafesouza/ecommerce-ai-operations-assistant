
from decimal import Decimal
from uuid import uuid4


def test_marketplace_profitability(client):
    sku = f"MARKETPLACE-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Amazon",
            "price": "29.90",
            "purchase_cost": "12.00",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/marketplace-profitability",
        params={
            "category": "backpacks",
            "fulfillment_fee": "3.50",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id

    assert Decimal(str(data["referral_fee"])) == Decimal("4.49")
    assert Decimal(str(data["fulfillment_fee"])) == Decimal("3.50")
    assert Decimal(str(data["estimated_profit"])) == Decimal("9.91")

def test_marketplace_profitability_custom_rate(client):
    sku = f"MARKETPLACE-CUSTOM-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Taxa Personalizada",
            "price": "100.00",
            "purchase_cost": "40.00",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/marketplace-profitability",
        params={
            "category": "backpacks",
            "fulfillment_fee": "5.00",
            "custom_rate_percent": "10.00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(str(data["referral_fee"])) == Decimal("10.00")
    assert Decimal(str(data["estimated_profit"])) == Decimal("45.00")
    assert Decimal(str(data["estimated_margin_percent"])) == Decimal("45.00")


def test_marketplace_profitability_unknown_category(client):
    sku = f"MARKETPLACE-CATEGORY-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Categoria Desconhecida",
            "price": "29.90",
            "purchase_cost": "12.00",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/marketplace-profitability",
        params={
            "category": "unknown_category",
            "fulfillment_fee": "3.50",
        },
    )

    assert response.status_code == 422
    assert "Unsupported category" in response.json()["detail"]


def test_marketplace_profitability_negative_fba_fee(client):
    sku = f"MARKETPLACE-FBA-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Taxa FBA Invalida",
            "price": "29.90",
            "purchase_cost": "12.00",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/marketplace-profitability",
        params={
            "category": "backpacks",
            "fulfillment_fee": "-3.50",
        },
    )

    assert response.status_code == 422

def test_marketplace_profitability_reference_date(client):
    sku = f"MARKETPLACE-DATE-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto com Data de Referencia",
            "price": "100.00",
            "purchase_cost": "40.00",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/marketplace-profitability",
        params={
            "category": "backpacks",
            "fulfillment_fee": "5.00",
            "reference_date": "2026-10-30",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id
    assert data["catalog_version"] == "2026-10-initial"
    assert data["reference_date"] == "2026-10-30"
    assert Decimal(str(data["referral_fee"])) == Decimal("15.00")
    assert Decimal(str(data["estimated_profit"])) == Decimal("40.00")

import pytest


@pytest.mark.parametrize(
    "reference_date",
    [
        "2025-01-01",
        "data-invalida",
    ],
)
def test_marketplace_profitability_invalid_reference_date(
    client,
    reference_date,
):
    sku = f"MARKETPLACE-DATE-INVALID-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Data Invalida",
            "price": "100.00",
            "purchase_cost": "40.00",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201
    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/marketplace-profitability",
        params={
            "category": "backpacks",
            "fulfillment_fee": "5.00",
            "reference_date": reference_date,
        },
    )

    assert response.status_code == 422
