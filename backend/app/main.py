
from decimal import Decimal
import math
from backend.app.marketplace_fees import calculate_referral_fee
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone, date
from fastapi import Query
from backend.app.database import get_db
from backend.app.models import Order, OrderItem, Product, StockMovement, Supplier
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.app.forecast_accuracy import calculate_forecast_accuracy
from backend.app.marketplace_fee_catalog import (
    AMAZON_FR_CATALOG,
    get_catalog_for_date,
)

from backend.app.schemas import (
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
)


app = FastAPI(
    title="E-commerce AI Operations Assistant",
    description="API for e-commerce operations and AI integration.",
    version="0.2.0",
)
# Frontend configuration
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)
@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")

# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "application": "E-commerce AI Operations Assistant",
        "version": "0.2.0",
    }


# --------------------------------------------------
# PRODUCTS
# --------------------------------------------------

@app.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):

    if product.supplier_id is not None:
        supplier = db.get(Supplier, product.supplier_id)

        if supplier is None:
            raise HTTPException(
                status_code=422,
                detail="Supplier not found",
            )

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

# --------------------------------------------------
# PRODUCTS - UPDATE
# --------------------------------------------------

@app.patch("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Only nullable fields can be explicitly cleared.
    non_nullable_fields = {
        "name",
        "price",
        "lead_time_days",
        "safety_stock",
    }

    for field in non_nullable_fields:
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )

    if update_data.get("supplier_id") is not None:
        supplier = db.get(
            Supplier,
            update_data["supplier_id"],
        )

        if supplier is None:
            raise HTTPException(
                status_code=422,
                detail="Supplier not found",
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update product",
        ) from exc

    return product

# --------------------------------------------------
# PRODUCTS - DELETE
# --------------------------------------------------

@app.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    order_item = db.scalar(
        select(OrderItem.id)
        .where(OrderItem.product_id == product_id)
        .limit(1)
    )

    if order_item is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a product associated with orders.",
        )

    stock_movement = db.scalar(
        select(StockMovement.id)
        .where(StockMovement.product_id == product_id)
        .limit(1)
    )

    if stock_movement is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a product with stock movements.",
        )

    try:
        db.delete(product)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a product with existing dependencies.",
        ) from exc


# --------------------------------------------------
# ORDERS - CREATE WITH INVENTORY CONTROL
# --------------------------------------------------

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

    # Reject duplicate products in the same order.
    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=422,
            detail="Duplicate products are not allowed.",
        )

    response_items = []
    total = Decimal("0.00")

    try:
        # Lock products in a consistent order.
        statement = (
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        )

        locked_products = db.scalars(statement).all()

        products_by_id = {
            product.id: product
            for product in locked_products
        }

        # Check products and inventory before creating the order.
        for item in order_data.items:
            product = products_by_id.get(item.product_id)

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found.",
                )

            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Insufficient stock for product {product.id}.",
                )

        new_order = Order(status="pending")
        db.add(new_order)
        db.flush()

        order_items = []

        for item in order_data.items:
            product = products_by_id[item.product_id]

            unit_price = product.price
            subtotal = unit_price * item.quantity
            total += subtotal

            # Deduct purchased quantity.
            product.stock_quantity -= item.quantity

            # Record inventory movement for this sale.
            db.add(
                StockMovement(
                    product_id=product.id,
                    order_id=new_order.id,
                    movement_type="sale",
                    quantity=-item.quantity,
                )
            )


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


# --------------------------------------------------
# ORDERS - RESPONSE HELPER
# --------------------------------------------------

def build_order_response(order: Order, db: Session) -> dict:
    statement = (
        select(OrderItem)
        .where(OrderItem.order_id == order.id)
        .order_by(OrderItem.id)
    )

    order_items = db.scalars(statement).all()

    response_items = []
    total = Decimal("0.00")

    for item in order_items:
        subtotal = item.unit_price * item.quantity
        total += subtotal

        response_items.append(
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": subtotal,
            }
        )

    return {
        "id": order.id,
        "status": order.status,
        "created_at": order.created_at,
        "total": total,
        "items": response_items,
    }


# --------------------------------------------------
# ORDERS - LIST
# --------------------------------------------------

@app.get("/orders", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db)):
    statement = select(Order).order_by(Order.id)

    orders = db.scalars(statement).all()

    return [
        build_order_response(order, db)
        for order in orders
    ]


# --------------------------------------------------
# ORDERS - GET BY ID
# --------------------------------------------------

@app.get("/orders/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found.",
        )

    return build_order_response(order, db)


# --------------------------------------------------
# ORDERS - STATUS MANAGEMENT
# --------------------------------------------------

@app.patch("/orders/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        # Lock the order to prevent simultaneous status changes.
        order = db.scalar(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        )

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )

        if order.status != "pending":
            raise HTTPException(
                status_code=409,
                detail="Only pending orders can change status",
            )

        if payload.status == "cancelled":
            # Retrieve items belonging to the order.
            order_items = db.scalars(
                select(OrderItem)
                .where(OrderItem.order_id == order.id)
                .order_by(OrderItem.product_id)
            ).all()

            # Lock all affected products before modifying stock.
            product_ids = [
                item.product_id for item in order_items
            ]

            locked_products = db.scalars(
                select(Product)
                .where(Product.id.in_(product_ids))
                .order_by(Product.id)
                .with_for_update()
            ).all()

            products_by_id = {
                product.id: product
                for product in locked_products
            }

            # Restore inventory within the same transaction.
            for item in order_items:
                product = products_by_id.get(item.product_id)

                if product is None:
                    raise HTTPException(
                        status_code=409,
                        detail="Product no longer exists",
                    )

                product.stock_quantity += item.quantity

                # Record inventory restoration caused by cancellation.
                db.add(
                    StockMovement(
                        product_id=product.id,
                        order_id=order.id,
                        movement_type="cancellation",
                        quantity=item.quantity,
                    )
                )


        order.status = payload.status

        db.commit()
        db.refresh(order)

        return build_order_response(order, db)

    except Exception:
        db.rollback()
        raise

# --------------------------------------------------
# ANALYTICS - SUMMARY
# --------------------------------------------------





@app.get("/analytics/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
):
    # Count all orders.
    total_orders = db.scalar(
        select(func.count()).select_from(Order)
    )

    # Count confirmed orders.
    confirmed_orders = db.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.status == "confirmed")
    )

    # Count cancelled orders.
    cancelled_orders = db.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.status == "cancelled")
    )

    # Calculate revenue from confirmed orders only.
    confirmed_revenue = db.scalar(
        select(
            func.sum(
                OrderItem.quantity * OrderItem.unit_price
            )
        )
        .select_from(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.status == "confirmed")
    )

    # Count products with 5 or fewer units in stock.
    low_stock_products = db.scalar(
        select(func.count())
        .select_from(Product)
        .where(Product.stock_quantity <= 5)
    )

    return {
        "total_orders": total_orders,
        "confirmed_orders": confirmed_orders,
        "cancelled_orders": cancelled_orders,
        "confirmed_revenue": str(
            confirmed_revenue or Decimal("0.00")
        ),
        "low_stock_products": low_stock_products,
    }

# --------------------------------------------------
# ANALYTICS - DEMAND FORECAST
# --------------------------------------------------

@app.get("/analytics/demand-forecast")
def get_demand_forecast(
    history_days: int = Query(default=30, ge=1, le=365),
    forecast_days: int = Query(default=14, ge=1, le=365),
    db: Session = Depends(get_db),
):
    start_date = datetime.now(timezone.utc) - timedelta(
        days=history_days
    )

    confirmed_sales = (
        select(
            OrderItem.product_id.label("product_id"),
            func.sum(OrderItem.quantity).label("units_sold"),
            func.count(func.distinct(Order.id)).label(
                "confirmed_order_count"
            ),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.status == "confirmed",
            Order.created_at >= start_date,
        )
        .group_by(OrderItem.product_id)
        .subquery()
    )

    statement = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            Product.stock_quantity,
            func.coalesce(
                confirmed_sales.c.units_sold, 0
            ).label("units_sold"),
            func.coalesce(
                confirmed_sales.c.confirmed_order_count, 0
            ).label("confirmed_order_count"),
        )
        .outerjoin(
            confirmed_sales,
            Product.id == confirmed_sales.c.product_id,
        )
        .order_by(Product.id)
    )

    rows = db.execute(statement).all()
    results = []

    for row in rows:
        units_sold = int(row.units_sold)
        confirmed_order_count = int(row.confirmed_order_count)

        average_daily_sales = units_sold / history_days

        forecast_quantity = max(
            0,
            math.ceil(average_daily_sales * forecast_days),
        )

        has_sales_history = confirmed_order_count > 0

        results.append(
            {
                "product_id": row.id,
                "sku": row.sku,
                "name": row.name,
                "stock_quantity": row.stock_quantity,
                "history_days": history_days,
                "forecast_days": forecast_days,
                "units_sold": units_sold,
                "confirmed_order_count": confirmed_order_count,
                "average_daily_sales": round(
                    average_daily_sales, 2
                ),
                "forecast_quantity": (
                    forecast_quantity
                    if has_sales_history
                    else None
                ),
                "forecast_method": "historical_daily_average",
                "data_status": (
                    "sales_history_available"
                    if has_sales_history
                    else "no_confirmed_sales"
                ),
            }
        )

    return results

# --------------------------------------------------
# INVENTORY - STOCK ALERTS
# --------------------------------------------------

@app.get("/inventory/alerts")
def get_inventory_alerts(
    db: Session = Depends(get_db),
):
    # Find products with 5 or fewer units available.
    statement = (
        select(Product)
        .where(Product.stock_quantity <= 5)
        .order_by(Product.id)
    )

    products = db.scalars(statement).all()

    alerts = []

    for product in products:
        if product.stock_quantity == 0:
            alert_level = "out_of_stock"
        else:
            alert_level = "low_stock"

        alerts.append(
            {
                "sku": product.sku,
                "name": product.name,
                "stock_quantity": product.stock_quantity,
                "alert_level": alert_level,
            }
        )

    return alerts

# --------------------------------------------------
# INVENTORY - SALES VELOCITY
# --------------------------------------------------


@app.get("/inventory/velocity")
def get_inventory_velocity(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Select only confirmed sales within the requested period.
    confirmed_sales = (
        select(
            OrderItem.product_id.label("product_id"),
            func.sum(OrderItem.quantity).label("units_sold"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.status == "confirmed",
            Order.created_at >= start_date,
        )
        .group_by(OrderItem.product_id)
        .subquery()
    )

    # Keep all products, including those without confirmed sales.
    statement = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            Product.stock_quantity,
            func.coalesce(
                confirmed_sales.c.units_sold, 0
            ).label("units_sold"),
        )
        .outerjoin(
            confirmed_sales,
            Product.id == confirmed_sales.c.product_id,
        )
        .order_by(Product.id)
    )

    rows = db.execute(statement).all()

    results = []

    for row in rows:
        units_sold = int(row.units_sold)

        results.append(
            {
                "product_id": row.id,
                "sku": row.sku,
                "name": row.name,
                "stock_quantity": row.stock_quantity,
                "units_sold": units_sold,
                "average_daily_sales": round(
                    units_sold / days, 2
                ),
            }
        )

    return results

# --------------------------------------------------
# INVENTORY - STOCK COVERAGE
# --------------------------------------------------

@app.get("/inventory/coverage")
def get_inventory_coverage(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    confirmed_sales = (
        select(
            OrderItem.product_id.label("product_id"),
            func.sum(OrderItem.quantity).label("units_sold"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.status == "confirmed",
            Order.created_at >= start_date,
        )
        .group_by(OrderItem.product_id)
        .subquery()
    )

    statement = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            Product.stock_quantity,
            func.coalesce(
                confirmed_sales.c.units_sold, 0
            ).label("units_sold"),
        )
        .outerjoin(
            confirmed_sales,
            Product.id == confirmed_sales.c.product_id,
        )
        .order_by(Product.id)
    )

    rows = db.execute(statement).all()
    results = []

    for row in rows:
        units_sold = int(row.units_sold)
        average_daily_sales = units_sold / days

        if average_daily_sales > 0:
            days_remaining = round(
                row.stock_quantity / average_daily_sales, 2
            )
        else:
            days_remaining = None

        results.append(
            {
                "product_id": row.id,
                "sku": row.sku,
                "name": row.name,
                "stock_quantity": row.stock_quantity,
                "units_sold": units_sold,
                "average_daily_sales": round(
                    average_daily_sales, 2
                ),
                "days_remaining": days_remaining,
            }
        )

    return results

# --------------------------------------------------
# INVENTORY - REPLENISHMENT RECOMMENDATIONS
# --------------------------------------------------


@app.get("/inventory/replenishment")
def get_inventory_replenishment(
    days: int = Query(default=30, ge=1, le=365),
    lead_time_days: int | None = Query(default=None, ge=1, le=365),
    safety_stock: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Calculate confirmed sales within the selected period.
    confirmed_sales = (
        select(
            OrderItem.product_id.label("product_id"),
            func.sum(OrderItem.quantity).label("units_sold"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.status == "confirmed",
            Order.created_at >= start_date,
        )
        .group_by(OrderItem.product_id)
        .subquery()
    )

    # Include all products and their individual inventory settings.
    statement = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            Product.stock_quantity,
            Product.lead_time_days,
            Product.safety_stock,
            func.coalesce(
                confirmed_sales.c.units_sold, 0
            ).label("units_sold"),
        )
        .outerjoin(
            confirmed_sales,
            Product.id == confirmed_sales.c.product_id,
        )
        .order_by(Product.id)
    )

    rows = db.execute(statement).all()
    results = []

    for row in rows:
        units_sold = int(row.units_sold)
        average_daily_sales = units_sold / days

        # URL parameters override individual settings when provided.
        effective_lead_time = (
            lead_time_days
            if lead_time_days is not None
            else row.lead_time_days
        )

        effective_safety_stock = (
            safety_stock
            if safety_stock is not None
            else row.safety_stock
        )

        expected_demand = (
            average_daily_sales * effective_lead_time
        )

        recommended_quantity = max(
            0,
            math.ceil(
                expected_demand
                + effective_safety_stock
                - row.stock_quantity
            ),
        )

        results.append(
            {
                "product_id": row.id,
                "sku": row.sku,
                "name": row.name,
                "stock_quantity": row.stock_quantity,
                "units_sold": units_sold,
                "average_daily_sales": round(
                    average_daily_sales, 2
                ),
                "lead_time_days": effective_lead_time,
                "safety_stock": effective_safety_stock,
                "recommended_quantity": recommended_quantity,
            }
        )

    return results

@app.post(
    "/suppliers",
    response_model=SupplierRead,
    status_code=201,
)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
):
    new_supplier = Supplier(**supplier.model_dump())

    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)

    return new_supplier

@app.get(
    "/suppliers",
    response_model=list[SupplierRead],
)
def list_suppliers(
    db: Session = Depends(get_db),
):
    suppliers = (
        db.query(Supplier)
        .order_by(Supplier.id)
        .all()
    )

    return suppliers

@app.get(
    "/suppliers/{supplier_id}",
    response_model=SupplierRead,
)
def get_supplier_by_id(
    supplier_id: int,
    db: Session = Depends(get_db),
):
    supplier = db.get(Supplier, supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return supplier

@app.patch(
    "/suppliers/{supplier_id}",
    response_model=SupplierRead,
)
def update_supplier(
    supplier_id: int,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
):
    supplier = db.get(Supplier, supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    update_data = supplier_update.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )

        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)

    return supplier

@app.get("/products/{product_id}/profitability")
def get_product_profitability(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    if product.purchase_cost is None:
        raise HTTPException(
            status_code=422,
            detail="Product purchase cost is not defined",
        )

    if product.price == 0:
        raise HTTPException(
            status_code=422,
            detail="Product selling price must be greater than zero",
        )

    gross_profit = product.price - product.purchase_cost

    gross_margin_percent = (
        gross_profit / product.price
    ) * Decimal("100")

    gross_margin_percent = gross_margin_percent.quantize(
        Decimal("0.01")
    )

    return {
        "product_id": product.id,
        "price": product.price,
        "purchase_cost": product.purchase_cost,
        "gross_profit": gross_profit,
        "gross_margin_percent": gross_margin_percent,
    }

@app.get("/products/{product_id}/marketplace-profitability")
def get_marketplace_profitability(
    product_id: int,
    category: str,
    fulfillment_fee: Decimal = Query(ge=0),
    custom_rate_percent: Decimal | None = Query(
        default=None,
        ge=0,
        le=100,
    ),
    reference_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    if product.purchase_cost is None:
        raise HTTPException(
            status_code=422,
            detail="Product purchase cost is not defined",
        )

    if product.price <= 0:
        raise HTTPException(
            status_code=422,
            detail="Product selling price must be greater than zero",
        )

    selected_date = reference_date if reference_date is not None else date.today()

    try:
        selected_catalog = get_catalog_for_date(
            [AMAZON_FR_CATALOG],
            selected_date,
        )

        referral_fee = calculate_referral_fee(
            category=category,
            price=product.price,
            marketplace="amazon.fr",
            custom_rate_percent=custom_rate_percent,
            catalog=selected_catalog,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    fulfillment_fee = fulfillment_fee.quantize(
        Decimal("0.01")
    )

    estimated_profit = (
        product.price
        - product.purchase_cost
        - referral_fee
        - fulfillment_fee
    ).quantize(Decimal("0.01"))

    estimated_margin_percent = (
        estimated_profit / product.price * Decimal("100")
    ).quantize(Decimal("0.01"))

    return {
        "product_id": product.id,
        "marketplace": selected_catalog.marketplace,
        "category": category,
        "catalog_version": selected_catalog.version,
        "reference_date": selected_date.isoformat(),
        "price": product.price,
        "purchase_cost": product.purchase_cost,
        "referral_fee": referral_fee,
        "fulfillment_fee": fulfillment_fee,
        "estimated_profit": estimated_profit,
        "estimated_margin_percent": estimated_margin_percent,
    }

# --------------------------------------------------
# ANALYTICS - FORECAST ACCURACY BACKTESTING
# --------------------------------------------------

@app.get("/analytics/forecast-accuracy")
def get_forecast_accuracy(
    history_days: int = Query(default=30, ge=1, le=365),
    forecast_days: int = Query(default=14, ge=1, le=365),
    db: Session = Depends(get_db),
):
    evaluation_end = datetime.now(timezone.utc)
    evaluation_start = evaluation_end - timedelta(
        days=forecast_days
    )
    history_start = evaluation_start - timedelta(
        days=history_days
    )

    def get_sales_by_product(start_date, end_date):
        statement = (
            select(
                OrderItem.product_id,
                func.sum(OrderItem.quantity).label("units_sold"),
                func.count(func.distinct(Order.id)).label(
                    "order_count"
                ),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                Order.status == "confirmed",
                Order.created_at >= start_date,
                Order.created_at < end_date,
            )
            .group_by(OrderItem.product_id)
        )

        rows = db.execute(statement).all()

        return {
            row.product_id: {
                "units_sold": int(row.units_sold),
                "order_count": int(row.order_count),
            }
            for row in rows
        }

    historical_sales = get_sales_by_product(
        history_start,
        evaluation_start,
    )

    observed_sales = get_sales_by_product(
        evaluation_start,
        evaluation_end,
    )

    products = db.execute(
        select(
            Product.id,
            Product.sku,
            Product.name,
        ).order_by(Product.id)
    ).all()

    results = []
    actual_values = []
    predicted_values = []

    for product in products:
        history = historical_sales.get(
            product.id,
            {"units_sold": 0, "order_count": 0},
        )
        observed = observed_sales.get(
            product.id,
            {"units_sold": 0, "order_count": 0},
        )

        history_units = history["units_sold"]
        actual_units = observed["units_sold"]

        has_history = history["order_count"] > 0

        predicted_units = (
            math.ceil(
                (history_units / history_days) * forecast_days
            )
            if has_history
            else None
        )

        absolute_error = (
            abs(actual_units - predicted_units)
            if predicted_units is not None
            else None
        )

        if predicted_units is not None:
            actual_values.append(actual_units)
            predicted_values.append(predicted_units)

        results.append(
            {
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "historical_units_sold": history_units,
                "actual_units_sold": actual_units,
                "predicted_units_sold": predicted_units,
                "absolute_error": absolute_error,
                "data_status": (
                    "evaluated"
                    if has_history
                    else "insufficient_history"
                ),
            }
        )

    metrics = (
        calculate_forecast_accuracy(
            actual_values,
            predicted_values,
        )
        if actual_values
        else None
    )

    return {
        "history_days": history_days,
        "forecast_days": forecast_days,
        "history_start": history_start,
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "forecast_method": "historical_daily_average",
        "metrics": metrics,
        "products": results,
    }
