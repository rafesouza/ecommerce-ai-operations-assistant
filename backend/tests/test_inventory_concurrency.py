
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from threading import Barrier, Event

from uuid import uuid4

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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

# Safety check: never run this test against the main database.
assert TEST_DATABASE_URL.database == "ecommerce_ai_test"

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
    # Create a unique SKU for each execution.
    sku = f"CONC-{uuid4().hex[:12]}"

    with TestSession.begin() as session:
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
        # Simulate two simultaneous purchases.
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(place_order)
                for _ in range(2)
            ]

            results = [
                future.result(timeout=30)
                for future in futures
            ]

        # One purchase succeeds, the other is rejected.
        assert sorted(results) == [201, 409]

        # Verify stock and order persistence.
        with TestSession() as session:
            saved_product = session.get(Product, product_id)

            assert saved_product is not None
            assert saved_product.stock_quantity == 0

            matching_items = session.scalars(
                select(OrderItem).where(
                    OrderItem.product_id == product_id
                )
            ).all()

            assert len(matching_items) == 1
            assert matching_items[0].quantity == 2

            saved_order = session.get(
                Order,
                matching_items[0].order_id,
            )

            assert saved_order is not None
            assert saved_order.status == "pending"

    finally:
        # Restore the application's original dependencies.
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

        # Remove only records created by this test.
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

def test_simultaneous_purchase_and_cancellation():
    # Use only the dedicated PostgreSQL test database.
    assert test_engine.url.database == "ecommerce_ai_test"

    sku = f"RACE-{uuid4().hex[:12]}"
    product_id = None

    # Create a product with 10 units.
    with TestSession.begin() as session:
        product = Product(
            sku=sku,
            name="Purchase and Cancellation Test",
            price=Decimal("79.90"),
            stock_quantity=10,
        )
        session.add(product)
        session.flush()
        product_id = product.id

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Create an order that reserves 3 units.
        with TestClient(app) as client:
            order_response = client.post(
                "/orders",
                json={
                    "items": [
                        {
                            "product_id": product_id,
                            "quantity": 3,
                        }
                    ]
                },
            )

        assert order_response.status_code == 201
        order_id = order_response.json()["id"]

        # Stock is now 7.
        with TestSession() as session:
            product = session.get(Product, product_id)
            assert product.stock_quantity == 7

        barrier = Barrier(2, timeout=15)

        def purchase():
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

        def cancel():
            with TestClient(app) as client:
                barrier.wait()
                response = client.patch(
                    f"/orders/{order_id}/status",
                    json={"status": "cancelled"},
                )
                return response.status_code

        # Start both operations concurrently.
        with ThreadPoolExecutor(max_workers=2) as executor:
            purchase_future = executor.submit(purchase)
            cancel_future = executor.submit(cancel)

            purchase_status = purchase_future.result(timeout=30)
            cancellation_status = cancel_future.result(timeout=30)

        assert purchase_status == 201
        assert cancellation_status == 200

        # Expected stock: 7 - 2 + 3 = 8.
        with TestSession() as session:
            product = session.get(Product, product_id)
            cancelled_order = session.get(Order, order_id)

            assert product.stock_quantity == 8
            assert cancelled_order.status == "cancelled"

            matching_items = session.scalars(
                select(OrderItem).where(
                    OrderItem.product_id == product_id
                )
            ).all()

            # One cancelled order and one new order.
            assert len(matching_items) == 2

    finally:
        # Restore application dependency overrides.
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

        # Delete only data belonging to this test.
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

def test_simultaneous_orders_with_reversed_product_order():
    assert test_engine.url.database == "ecommerce_ai_test"

    product_ids = []
    original_overrides = app.dependency_overrides.copy()

    try:
        # Create two independent test products.
        with TestSession.begin() as session:
            for name in ("Backpack", "Bag"):
                product = Product(
                    sku=f"MULTI-{uuid4().hex[:12]}",
                    name=name,
                    price=Decimal("49.90"),
                    stock_quantity=2,
                )
                session.add(product)
                session.flush()
                product_ids.append(product.id)

        app.dependency_overrides[get_db] = override_get_db
        barrier = Barrier(2, timeout=15)

        def place_order(ids):
            with TestClient(app) as client:
                barrier.wait()
                response = client.post(
                    "/orders",
                    json={
                        "items": [
                            {"product_id": ids[0], "quantity": 1},
                            {"product_id": ids[1], "quantity": 1},
                        ]
                    },
                )
                return response.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(place_order, product_ids)
            second = executor.submit(
                place_order,
                list(reversed(product_ids)),
            )

            results = [
                first.result(timeout=30),
                second.result(timeout=30),
            ]

        assert results == [201, 201]

        with TestSession() as session:
            for product_id in product_ids:
                product = session.get(Product, product_id)
                assert product.stock_quantity == 0

            items = session.scalars(
                select(OrderItem).where(
                    OrderItem.product_id.in_(product_ids)
                )
            ).all()

            assert len(items) == 4
            assert len({item.order_id for item in items}) == 2

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

        if product_ids:
            with TestSession.begin() as session:
                order_ids = session.scalars(
                    select(OrderItem.order_id)
                    .where(OrderItem.product_id.in_(product_ids))
                ).all()

                if order_ids:
                    session.query(OrderItem).filter(
                        OrderItem.order_id.in_(order_ids)
                    ).delete(synchronize_session=False)

                    session.query(Order).filter(
                        Order.id.in_(order_ids)
                    ).delete(synchronize_session=False)

                session.query(Product).filter(
                    Product.id.in_(product_ids)
                ).delete(synchronize_session=False)
