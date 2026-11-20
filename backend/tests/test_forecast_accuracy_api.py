
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import get_db
from backend.app.main import app
from backend.app.models import (
    Base,
    Order,
    OrderItem,
    Product,
)


@pytest.fixture
def test_database():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield engine, client
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def add_order(
    session,
    product_id,
    quantity,
    created_at,
    status="confirmed",
):
    order = Order(
        status=status,
        created_at=created_at,
    )
    session.add(order)
    session.flush()

    session.add(
        OrderItem(
            order_id=order.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=Decimal("10.00"),
        )
    )


def test_backtesting_separates_historical_and_actual_sales(
    test_database,
):
    engine, client = test_database
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        product = Product(
            sku="FORECAST-001",
            name="Forecast Test Product",
            price=Decimal("10.00"),
            stock_quantity=20,
        )
        session.add(product)
        session.flush()

        # Historical period: 30 days before evaluation.
        add_order(
            session,
            product.id,
            6,
            now - timedelta(days=20),
        )

        # Evaluation period: most recent 14 days.
        add_order(
            session,
            product.id,
            5,
            now - timedelta(days=5),
        )

        # Pending orders must not count.
        add_order(
            session,
            product.id,
            100,
            now - timedelta(days=4),
            status="pending",
        )

        # Orders outside both periods must not count.
        add_order(
            session,
            product.id,
            50,
            now - timedelta(days=60),
        )

        session.commit()

    response = client.get(
        "/analytics/forecast-accuracy",
        params={
            "history_days": 30,
            "forecast_days": 14,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["history_days"] == 30
    assert data["forecast_days"] == 14
    assert data["forecast_method"] == "historical_daily_average"

    product = data["products"][0]

    assert product["historical_units_sold"] == 6
    assert product["actual_units_sold"] == 5
    assert product["predicted_units_sold"] == 3
    assert product["absolute_error"] == 2
    assert product["data_status"] == "evaluated"

    assert data["metrics"]["observation_count"] == 1
    assert data["metrics"]["mae"] == 2
    assert data["metrics"]["wape"] == 40.0


def test_backtesting_handles_missing_sales_history(
    test_database,
):
    engine, client = test_database
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        product = Product(
            sku="FORECAST-002",
            name="New Product",
            price=Decimal("15.00"),
            stock_quantity=10,
        )
        session.add(product)
        session.flush()

        add_order(
            session,
            product.id,
            4,
            now - timedelta(days=3),
        )

        session.commit()

    response = client.get("/analytics/forecast-accuracy")

    assert response.status_code == 200

    data = response.json()
    product = data["products"][0]

    assert product["historical_units_sold"] == 0
    assert product["actual_units_sold"] == 4
    assert product["predicted_units_sold"] is None
    assert product["absolute_error"] is None
    assert product["data_status"] == "insufficient_history"
    assert data["metrics"] is None


@pytest.mark.parametrize(
    "params",
    [
        {"history_days": 0},
        {"history_days": 366},
        {"forecast_days": 0},
        {"forecast_days": 366},
    ],
)
def test_backtesting_rejects_invalid_periods(
    test_database,
    params,
):
    _, client = test_database

    response = client.get(
        "/analytics/forecast-accuracy",
        params=params,
    )

    assert response.status_code == 422
