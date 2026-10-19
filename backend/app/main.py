
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Order, OrderItem, Product
from backend.app.schemas import (
    OrderCreate,
    OrderRead,
    ProductCreate,
    ProductRead,
)


app = FastAPI(
    title="E-commerce AI Operations Assistant",
    description="API for e-commerce operations and AI integration.",
    version="0.2.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "application": "E-commerce AI Operations Assistant",
        "version": "0.2.0",
    }


@app.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):
    new_product = Product(**product.model_dump())

    db.add(new_product)

    try:
        db.commit()
        db.refresh(new_product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A product with this SKU already exists.",
        )

    return new_product


@app.get("/products", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)):
    statement = select(Product).order_by(Product.id)
    return db.scalars(statement).all()


@app.get("/products/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    return product

@app.post(
    "/orders",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
):
    product_ids = [
        item.product_id for item in order_data.items
    ]

    # Prevent duplicate products within one order.
    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=422,
            detail="Duplicate products are not allowed.",
        )

    order_items = []
    response_items = []
    total = 0

    try:
        # Create the order header.
        new_order = Order(status="pending")
        db.add(new_order)
        db.flush()

        for item in order_data.items:
            product = db.get(Product, item.product_id)

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found.",
                )

            unit_price = product.price
            subtotal = unit_price * item.quantity
            total += subtotal

            order_items.append(
                OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                )
            )

            response_items.append(
                {
                    "product_id": product.id,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "subtotal": subtotal,
                }
            )

        db.add_all(order_items)
        db.commit()
        db.refresh(new_order)

        return {
            "id": new_order.id,
            "status": new_order.status,
            "created_at": new_order.created_at,
            "total": total,
            "items": response_items,
        }

    except Exception:
        db.rollback()
        raise
