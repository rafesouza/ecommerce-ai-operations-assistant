
from backend.app.models import Order, Product
from decimal import Decimal


def test_analytics_summary_counts_orders(client):
    # Create two orders directly in the test database.
    session_factory = client.testing_session_factory

    with session_factory.begin() as session:
        session.add_all([
            Order(status="pending"),
            Order(status="confirmed"),
        ])

    response = client.get("/analytics/summary")

    assert response.status_code == 200
    assert response.json()["total_orders"] == 2

def test_analytics_summary_counts_confirmed_orders(client):
    session_factory = client.testing_session_factory

    with session_factory.begin() as session:
        session.add_all([
            Order(status="pending"),
            Order(status="pending"),
            Order(status="confirmed"),
            Order(status="confirmed"),
            Order(status="confirmed"),
            Order(status="cancelled"),
        ])

    response = client.get("/analytics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 6
    assert data["confirmed_orders"] == 3

def test_analytics_summary_counts_cancelled_orders(client):
    session_factory = client.testing_session_factory

    with session_factory.begin() as session:
        session.add_all([
            Order(status="pending"),
            Order(status="confirmed"),
            Order(status="confirmed"),
            Order(status="cancelled"),
            Order(status="cancelled"),
            Order(status="cancelled"),
        ])

    response = client.get("/analytics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 6
    assert data["confirmed_orders"] == 2
    assert data["cancelled_orders"] == 3

def test_analytics_summary_calculates_confirmed_revenue(client):
    from backend.app.models import OrderItem, Product

    with client.testing_session_factory.begin() as session:
        product = Product(
            sku="ANALYTICS-REVENUE-001",
            name="Test Backpack",
            price=Decimal("79.90"),
            stock_quantity=10,
        )
        session.add(product)
        session.flush()

        confirmed_order = Order(status="confirmed")
        pending_order = Order(status="pending")
        session.add_all([confirmed_order, pending_order])
        session.flush()

        session.add_all([
            OrderItem(
                order_id=confirmed_order.id,
                product_id=product.id,
                quantity=2,
                unit_price=Decimal("79.90"),
            ),
            OrderItem(
                order_id=pending_order.id,
                product_id=product.id,
                quantity=1,
                unit_price=Decimal("79.90"),
            ),
        ])

    response = client.get("/analytics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 2
    assert data["confirmed_orders"] == 1
    assert data["cancelled_orders"] == 0
    assert Decimal(str(data["confirmed_revenue"])) == Decimal("159.80")

def test_analytics_summary_returns_zero_revenue_without_confirmed_orders(client):
    session_factory = client.testing_session_factory

    with session_factory.begin() as session:
        session.add_all([
            Order(status="pending"),
            Order(status="cancelled"),
        ])

    response = client.get("/analytics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 2
    assert data["confirmed_orders"] == 0
    assert data["cancelled_orders"] == 1
    assert Decimal(str(data["confirmed_revenue"])) == Decimal("0.00")

def test_analytics_summary_counts_low_stock_products(client):
    with client.testing_session_factory.begin() as session:
        session.add_all([
            Product(
                sku="STOCK-ANALYTICS-001",
                name="Premium Backpack",
                price=Decimal("109.00"),
                stock_quantity=20,
            ),
            Product(
                sku="STOCK-ANALYTICS-002",
                name="Aromatic Candle",
                price=Decimal("29.90"),
                stock_quantity=5,
            ),
            Product(
                sku="STOCK-ANALYTICS-003",
                name="Groovy Bag",
                price=Decimal("99.00"),
                stock_quantity=2,
            ),
            Product(
                sku="STOCK-ANALYTICS-004",
                name="Timtim Plush",
                price=Decimal("24.90"),
                stock_quantity=0,
            ),
        ])

    response = client.get("/analytics/summary")

    assert response.status_code == 200
    assert response.json()["low_stock_products"] == 3
