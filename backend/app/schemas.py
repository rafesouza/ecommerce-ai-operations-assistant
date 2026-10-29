
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    stock_quantity: int = Field(ge=0)

    lead_time_days: int = Field(default=7, ge=1, le=365)
    safety_stock: int = Field(default=5, ge=0)

    supplier_id: int | None = Field(default=None, gt=0)


class ProductRead(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderRead(BaseModel):
    id: int
    status: str
    created_at: datetime
    total: Decimal
    items: list[OrderItemRead]


class OrderStatusUpdate(BaseModel):
    status: Literal["confirmed", "cancelled"]


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=255)
    lead_time_days: int = Field(default=7, ge=1, le=365)


class SupplierRead(SupplierCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SupplierUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    email: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )
    lead_time_days: int | None = Field(
        default=None,
        ge=1,
        le=365,
    )
