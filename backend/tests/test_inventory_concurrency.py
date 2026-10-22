
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from backend.app.database import get_db
from backend.app.main import app

from backend.app.models import Order, OrderItem, Product


load_dotenv()

TEST_DATABASE_URL = URL.create(
    "postgresql+psycopg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="127.0.0.1",
    port=int(os.environ.get("POSTGRES_PORT", "5433")),
    database="ecommerce_ai_test",
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_size=5,
    max_overflow=0,
)

TestSession = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


def override_get_db():
    with TestSession() as session:
        yield session


def test_simultaneous_orders_do_not_oversell():
    # Use an isolated SKU; do not delete existing test data.
    sku = f"CONC-{uuid4().hex[:12]}"

    with TestSession.begin() as session:
        existing = session.scalar(
            select(Product).where(Product.sku == sku)
        )

        assert existing is None, (
            "Test SKU already exists. Use a new test SKU."
        )

        product = Product(
            sku=sku,
            name="Concurrency Test Backpack",
            price=Decimal("79.90"),
            stock_quantity=2,
        )
        session.add(product)
        session.flush()
        product_id = product.id

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    barrier = Barrier(2, timeout=15)

    def place_order():
        with TestClient(app) as client:
            barrier.wait()
            response = client.post(
                "/orders",
                json={
                    "items": [
                        {
                            "product_id": product_id,
                            "quantity": 2,
                        }
                    ]
                },
            )
            return response.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(place_order)
                for _ in range(2)
            ]
            results = [
                future.result(timeout=30)
                for future in futures
            ]

        assert sorted(results) == [201, 409]

        with TestSession() as session:
            saved_product = session.get(Product, product_id)
            assert saved_product.stock_quantity == 0

            orders = session.scalars(
                select(Order)
            ).all()

            matching_orders = [
                order for order in orders
                if any(
                    item.product_id == product_id
                    for item in session.execute(
                        select_order_items(order.id)
                    ).scalars()
                )
            ]

            assert len(matching_orders) == 1
      finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

        # Clean up only records created by this test.
        with TestSession.begin() as session:
            order_ids = session.scalars(
                select(OrderItem.order_id).where(
                    OrderItem.product_id == product_id
                )
            ).all()

            if order_ids:
                session.query(OrderItem).filter(
                    OrderItem.order_id.in_(order_ids)
                ).delete(synchronize_session=False)

                session.query(Order).filter(
                    Order.id.in_(order_ids)
                ).delete(synchronize_session=False)

            product = session.get(Product, product_id)

            if product is not None:
                session.delete(product)


def select_order_items(order_id):
    from backend.app.models import OrderItem

    return select(OrderItem).where(
        OrderItem.order_id == order_id
    )
