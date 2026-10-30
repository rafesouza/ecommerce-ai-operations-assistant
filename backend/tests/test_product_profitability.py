
from decimal import Decimal
from uuid import uuid4


def test_product_profitability(client):
    sku = f"PROFIT-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Lucratividade",
            "price": "29.90",
            "purchase_cost": "12.00",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/profitability"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id

    assert Decimal(str(data["price"])) == Decimal("29.90")
    assert Decimal(str(data["purchase_cost"])) == Decimal("12.00")

    assert Decimal(str(data["gross_profit"])) == Decimal("17.90")
    assert Decimal(str(data["gross_margin_percent"])) == Decimal("59.87")

def test_product_profitability_not_found(client):
    response = client.get(
        "/products/999999999/profitability"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product not found"
    }


def test_product_profitability_without_purchase_cost(client):
    sku = f"PROFIT-NO-COST-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Sem Custo",
            "price": "29.90",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/profitability"
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Product purchase cost is not defined"
    }


def test_product_profitability_zero_price(client):
    sku = f"PROFIT-ZERO-{uuid4().hex[:12]}"

    create_response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Preco Zero",
            "price": "0.00",
            "purchase_cost": "12.00",
            "stock_quantity": 10,
        },
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}/profitability"
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Product selling price must be greater than zero"
    }
