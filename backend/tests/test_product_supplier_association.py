
from decimal import Decimal


def test_create_product_with_supplier(client):
    supplier_response = client.post(
        "/suppliers",
        json={
            "name": "Luminante",
            "email": "contact@example.com",
            "lead_time_days": 7,
        },
    )

    assert supplier_response.status_code == 201
    supplier_id = supplier_response.json()["id"]

    product_response = client.post(
        "/products",
        json={
            "sku": "VELA-SUPPLIER-001",
            "name": "Vela Aromatica",
            "price": "24.90",
            "stock_quantity": 20,
            "supplier_id": supplier_id,
        },
    )

    assert product_response.status_code == 201

    product = product_response.json()

    assert product["supplier_id"] == supplier_id
    assert product["sku"] == "VELA-SUPPLIER-001"
    assert Decimal(str(product["price"])) == Decimal("24.90")

def test_create_product_with_nonexistent_supplier(client):
    response = client.post(
        "/products",
        json={
            "sku": "VELA-INVALID-SUPPLIER-001",
            "name": "Vela Fornecedor Inexistente",
            "price": "24.90",
            "stock_quantity": 10,
            "supplier_id": 999999999,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Supplier not found"
    }

def test_create_product_without_supplier(client):
    response = client.post(
        "/products",
        json={
            "sku": "PRODUCT-NO-SUPPLIER-001",
            "name": "Produto Sem Fornecedor",
            "price": "19.90",
            "stock_quantity": 15,
        },
    )

    assert response.status_code == 201

    product = response.json()

    assert product["supplier_id"] is None
    assert product["sku"] == "PRODUCT-NO-SUPPLIER-001"
    assert product["name"] == "Produto Sem Fornecedor"
