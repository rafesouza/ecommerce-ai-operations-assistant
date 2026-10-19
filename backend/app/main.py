
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Product
from backend.app.schemas import ProductCreate, ProductRead


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
