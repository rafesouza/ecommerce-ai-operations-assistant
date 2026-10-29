
def test_create_supplier(client):
    response = client.post(
        "/suppliers",
        json={
            "name": "Luminante",
            "email": "contact@example.com",
            "lead_time_days": 7,
        },
    )

    assert response.status_code == 201

    supplier = response.json()

    assert isinstance(supplier["id"], int)
    assert supplier["name"] == "Luminante"
    assert supplier["email"] == "contact@example.com"
    assert supplier["lead_time_days"] == 7

import pytest


@pytest.mark.parametrize(
    "invalid_data",
    [
        {
            "name": "",
            "email": "contact@example.com",
            "lead_time_days": 7,
        },
        {
            "name": "Luminante",
            "email": "contact@example.com",
            "lead_time_days": -1,
        },
        {
            "name": "Luminante",
            "email": "contact@example.com",
            "lead_time_days": 366,
        },
    ],
)
def test_create_supplier_invalid_data(client, invalid_data):
    response = client.post(
        "/suppliers",
        json=invalid_data,
    )

    assert response.status_code == 422

def test_list_suppliers(client):
    create_response = client.post(
        "/suppliers",
        json={
            "name": "Fornecedor Teste Lista",
            "email": "lista@example.com",
            "lead_time_days": 10,
        },
    )

    assert create_response.status_code == 201

    supplier_id = create_response.json()["id"]

    response = client.get("/suppliers")

    assert response.status_code == 200

    suppliers = response.json()

    assert isinstance(suppliers, list)

    assert any(
        supplier["id"] == supplier_id
        and supplier["name"] == "Fornecedor Teste Lista"
        and supplier["email"] == "lista@example.com"
        and supplier["lead_time_days"] == 10
        for supplier in suppliers
    )

def test_get_supplier_by_id(client):
    create_response = client.post(
        "/suppliers",
        json={
            "name": "Fornecedor Individual",
            "email": "individual@example.com",
            "lead_time_days": 12,
        },
    )

    assert create_response.status_code == 201

    supplier_id = create_response.json()["id"]

    response = client.get(f"/suppliers/{supplier_id}")

    assert response.status_code == 200

    supplier = response.json()

    assert supplier["id"] == supplier_id
    assert supplier["name"] == "Fornecedor Individual"
    assert supplier["email"] == "individual@example.com"
    assert supplier["lead_time_days"] == 12

def test_get_supplier_not_found(client):
    response = client.get("/suppliers/999999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Supplier not found"
    }

def test_update_supplier(client):
    create_response = client.post(
        "/suppliers",
        json={
            "name": "Fornecedor Original",
            "email": "original@example.com",
            "lead_time_days": 7,
        },
    )

    assert create_response.status_code == 201

    supplier_id = create_response.json()["id"]

    response = client.patch(
        f"/suppliers/{supplier_id}",
        json={
            "email": "atualizado@example.com",
            "lead_time_days": 15,
        },
    )

    assert response.status_code == 200

    updated_supplier = response.json()

    assert updated_supplier["id"] == supplier_id
    assert updated_supplier["name"] == "Fornecedor Original"
    assert updated_supplier["email"] == "atualizado@example.com"
    assert updated_supplier["lead_time_days"] == 15

    get_response = client.get(f"/suppliers/{supplier_id}")

    assert get_response.status_code == 200
    assert get_response.json()["email"] == "atualizado@example.com"
    assert get_response.json()["lead_time_days"] == 15

def test_update_supplier_not_found(client):
    response = client.patch(
        "/suppliers/999999999",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Supplier not found"
    }


@pytest.mark.parametrize(
    "invalid_data",
    [
        {"lead_time_days": -1},
        {"lead_time_days": None},
        {"name": ""},
    ],
)
def test_update_supplier_invalid_data(client, invalid_data):
    create_response = client.post(
        "/suppliers",
        json={
            "name": "Fornecedor Validação",
            "email": "validacao@example.com",
            "lead_time_days": 7,
        },
    )

    assert create_response.status_code == 201

    supplier_id = create_response.json()["id"]

    response = client.patch(
        f"/suppliers/{supplier_id}",
        json=invalid_data,
    )

    assert response.status_code == 422
