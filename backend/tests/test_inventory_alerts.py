
from decimal import Decimal

from backend.app.models import Product


def test_inventory_alerts_returns_low_stock_products(client):
    with client.testing_session_factory.begin() as session:
        session.add_all([
            Product(
                sku="ALERT-001",
                name="Premium Backpack",
                price=Decimal("109.00"),
                stock_quantity=15,
            ),
            Product(
                sku="ALERT-002",
                name="Aromatic Candle",
                price=Decimal("29.90"),
                stock_quantity=4,
            ),
            Product(
                sku="ALERT-003",
                name="Timtim Plush",
                price=Decimal("24.90"),
                stock_quantity=0,
            ),
        ])

    response = client.get("/inventory/alerts")

    assert response.status_code == 200

    alerts = response.json()

    assert len(alerts) == 2

    assert alerts[0]["sku"] == "ALERT-002"
    assert alerts[0]["name"] == "Aromatic Candle"
    assert alerts[0]["stock_quantity"] == 4
    assert alerts[0]["alert_level"] == "low_stock"

    assert alerts[1]["sku"] == "ALERT-003"
    assert alerts[1]["name"] == "Timtim Plush"
    assert alerts[1]["stock_quantity"] == 0
    assert alerts[1]["alert_level"] == "out_of_stock"

def test_inventory_alerts_returns_empty_when_stock_is_normal(client):
    with client.testing_session_factory.begin() as session:
        session.add_all([
            Product(
                sku="NORMAL-001",
                name="Premium Backpack",
                price=Decimal("109.00"),
                stock_quantity=20,
            ),
            Product(
                sku="NORMAL-002",
                name="Aromatic Candle",
                price=Decimal("29.90"),
                stock_quantity=10,
            ),
            Product(
                sku="NORMAL-003",
                name="Groovy Bag",
                price=Decimal("99.00"),
                stock_quantity=6,
            ),
        ])

    response = client.get("/inventory/alerts")

    assert response.status_code == 200
    assert response.json() == []

def test_inventory_alerts_returns_empty_without_products(client):
    response = client.get("/inventory/alerts")

    assert response.status_code == 200
    assert response.json() == []
