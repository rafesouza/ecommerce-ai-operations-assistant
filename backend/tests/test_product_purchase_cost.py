
from decimal import Decimal
from uuid import uuid4


def test_create_product_with_purchase_cost(client):
    sku = f"COST-{uuid4().hex[:12]}"

    response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto com Custo",
            "price": "29.90",
            "purchase_cost": "12.00",
            "stock_quantity": 20,
        },
    )

    assert response.status_code == 201

    product = response.json()

    assert product["sku"] == sku
    assert Decimal(str(product["price"])) == Decimal("29.90")
    assert Decimal(str(product["purchase_cost"])) == Decimal("12.00")
    assert product["stock_quantity"] == 20

def test_create_product_without_purchase_cost(client):
    sku = f"COST-OPTIONAL-{uuid4().hex[:12]}"

    response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto Sem Custo",
            "price": "29.90",
            "stock_quantity": 10,
        },
    )

    assert response.status_code == 201

    product = response.json()

    assert product["sku"] == sku
    assert product["purchase_cost"] is None


def test_create_product_with_negative_purchase_cost(client):
    sku = f"COST-INVALID-{uuid4().hex[:12]}"

    response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Produto com Custo Invalido",
            "price": "29.90",
            "purchase_cost": "-5.00",
            "stock_quantity": 10,
        },
    )

    assert response.status_code == 422
