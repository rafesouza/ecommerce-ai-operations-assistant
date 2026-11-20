
from decimal import Decimal

from backend.app.models import Order, OrderItem, Product


def create_test_product(session, sku="FORECAST-001"):
    product = Product(
        sku=sku,
        name="Forecast Test Backpack",
        price=Decimal("79.90"),
        stock_quantity=20,
    )
    session.add(product)
    session.flush()
    return product


def test_forecast_calculates_expected_demand(client):
    with client.testing_session_factory.begin() as session:
        product = create_test_product(session)

        order = Order(status="confirmed")
        session.add(order)
        session.flush()

        session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=60,
                unit_price=Decimal("79.90"),
            )
        )

    response = client.get(
        "/analytics/demand-forecast"
        "?history_days=30&forecast_days=14"
    )

    assert response.status_code == 200

    data = response.json()[0]

    assert data["units_sold"] == 60
    assert data["confirmed_order_count"] == 1
    assert data["average_daily_sales"] == 2.0
    assert data["forecast_quantity"] == 28
    assert data["forecast_method"] == "historical_daily_average"
    assert data["data_status"] == "sales_history_available"


def test_forecast_ignores_unconfirmed_orders(client):
    with client.testing_session_factory.begin() as session:
        product = create_test_product(session)

        confirmed = Order(status="confirmed")
        pending = Order(status="pending")
        cancelled = Order(status="cancelled")

        session.add_all([confirmed, pending, cancelled])
        session.flush()

        for order in [confirmed, pending, cancelled]:
            session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=10,
                    unit_price=Decimal("79.90"),
                )
            )

    response = client.get(
        "/analytics/demand-forecast"
        "?history_days=10&forecast_days=10"
    )

    assert response.status_code == 200

    data = response.json()[0]

    assert data["units_sold"] == 10
    assert data["confirmed_order_count"] == 1
    assert data["forecast_quantity"] == 10


def test_forecast_handles_no_sales_history(client):
    with client.testing_session_factory.begin() as session:
        create_test_product(session)

    response = client.get("/analytics/demand-forecast")

    assert response.status_code == 200

    data = response.json()[0]

    assert data["units_sold"] == 0
    assert data["confirmed_order_count"] == 0
    assert data["average_daily_sales"] == 0
    assert data["forecast_quantity"] is None
    assert data["data_status"] == "no_confirmed_sales"


def test_forecast_validates_periods(client):
    invalid_queries = [
        "?history_days=0",
        "?history_days=366",
        "?forecast_days=0",
        "?forecast_days=366",
    ]

    for query in invalid_queries:
        response = client.get(
            f"/analytics/demand-forecast{query}"
        )

        assert response.status_code == 422


def test_forecast_returns_all_products(client):
    with client.testing_session_factory.begin() as session:
        create_test_product(session, "FORECAST-001")
        create_test_product(session, "FORECAST-002")

    response = client.get("/analytics/demand-forecast")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {item["sku"] for item in data} == {
        "FORECAST-001",
        "FORECAST-002",
    }
