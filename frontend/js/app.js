
"use strict";

const productsTableBody = document.getElementById(
    "products-table-body"
);

const totalProductsElement = document.getElementById(
    "total-products"
);

const refreshButton = document.getElementById(
    "refresh-button"
);

const currencyFormatter = new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR"
});

function showTableMessage(message) {
    productsTableBody.replaceChildren();

    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = 5;
    cell.textContent = message;

    row.appendChild(cell);
    productsTableBody.appendChild(row);
}

function renderProducts(products) {
    productsTableBody.replaceChildren();

    totalProductsElement.textContent = String(products.length);

    if (products.length === 0) {
        showTableMessage("No products registered yet.");
        return;
    }

    for (const product of products) {
        const row = document.createElement("tr");

        const values = [
            product.id,
            product.sku,
            product.name,
            currencyFormatter.format(Number(product.price)),
            product.stock_quantity
        ];

        for (const value of values) {
            const cell = document.createElement("td");
            cell.textContent = String(value ?? "—");
            row.appendChild(cell);
        }

        productsTableBody.appendChild(row);
    }
}

async function loadProducts() {
    refreshButton.disabled = true;
    refreshButton.textContent = "Loading...";

    showTableMessage("Loading products...");

    try {
        const response = await fetch("/products", {
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(
                `API returned HTTP ${response.status}`
            );
        }

        const products = await response.json();

        if (!Array.isArray(products)) {
            throw new Error("Unexpected products response.");
        }

        renderProducts(products);
    } catch (error) {
        console.error("Failed to load products:", error);

        totalProductsElement.textContent = "—";

        showTableMessage(
            "Unable to load products. Check the API connection."
        );
    } finally {
        refreshButton.disabled = false;
        refreshButton.textContent = "Refresh Data";
    }
}

refreshButton.addEventListener("click", () => {
    loadProducts();
    loadDashboardMetrics();
});

document.addEventListener("DOMContentLoaded", loadProducts);

async function loadDashboardMetrics() {
    const totalOrdersElement = document.getElementById(
        "total-orders"
    );

    const lowStockElement = document.getElementById(
        "low-stock-products"
    );

    const revenueElement = document.getElementById(
        "confirmed-revenue"
    );

    try {
        const response = await fetch("/analytics/summary", {
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(
                `Analytics API returned HTTP ${response.status}`
            );
        }

        const data = await response.json();

        if (
            typeof data.total_orders !== "number" ||
            typeof data.low_stock_products !== "number" ||
            data.confirmed_revenue == null ||
            !Number.isFinite(Number(data.confirmed_revenue))
        ) {
            throw new Error("Unexpected analytics response.");
        }

        totalOrdersElement.textContent = String(
            data.total_orders
        );

        lowStockElement.textContent = String(
            data.low_stock_products
        );

        revenueElement.textContent = currencyFormatter.format(
            Number(data.confirmed_revenue)
        );

    } catch (error) {
        console.error("Failed to load dashboard metrics:", error);

        totalOrdersElement.textContent = "—";
        lowStockElement.textContent = "—";
        revenueElement.textContent = "—";
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadDashboardMetrics
);

const ordersTableBody = document.getElementById(
    "orders-table-body"
);

const refreshOrdersButton = document.getElementById(
    "refresh-orders-button"
);

function showOrdersMessage(message) {
    ordersTableBody.replaceChildren();

    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = 5;
    cell.textContent = message;

    row.appendChild(cell);
    ordersTableBody.appendChild(row);
}

function renderOrders(orders) {
    ordersTableBody.replaceChildren();

    if (orders.length === 0) {
        showOrdersMessage("No orders registered yet.");
        return;
    }

    for (const order of orders) {
        const row = document.createElement("tr");

        const date = new Date(order.created_at);

        const formattedDate = Number.isNaN(date.getTime())
            ? "—"
            : date.toLocaleDateString("fr-FR");

        const itemCount = Array.isArray(order.items)
            ? order.items.reduce(
                (sum, item) => sum + Number(item.quantity || 0),
                0
            )
            : 0;

        const total = Number(order.total);

        const values = [
            order.id,
            formattedDate,
            order.status,
            itemCount,
            Number.isFinite(total)
                ? currencyFormatter.format(total)
                : "—"
        ];

        for (const value of values) {
            const cell = document.createElement("td");
            cell.textContent = String(value ?? "—");
            row.appendChild(cell);
        }

        ordersTableBody.appendChild(row);
    }
}

async function loadOrders() {
    refreshOrdersButton.disabled = true;
    refreshOrdersButton.textContent = "Loading...";

    showOrdersMessage("Loading orders...");

    try {
        const response = await fetch("/orders", {
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(
                `Orders API returned HTTP ${response.status}`
            );
        }

        const orders = await response.json();

        if (!Array.isArray(orders)) {
            throw new Error("Unexpected orders response.");
        }

        renderOrders(orders);
    } catch (error) {
        console.error("Failed to load orders:", error);

        showOrdersMessage(
            "Unable to load orders. Check the API connection."
        );
    } finally {
        refreshOrdersButton.disabled = false;
        refreshOrdersButton.textContent = "Refresh Orders";
    }
}

refreshOrdersButton.addEventListener("click", () => {
    loadOrders();
    loadDashboardMetrics();
});

document.addEventListener("DOMContentLoaded", loadOrders);

const suppliersTableBody = document.getElementById(
    "suppliers-table-body"
);

const refreshSuppliersButton = document.getElementById(
    "refresh-suppliers-button"
);

function showSuppliersMessage(message) {
    suppliersTableBody.replaceChildren();

    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = 4;
    cell.textContent = message;

    row.appendChild(cell);
    suppliersTableBody.appendChild(row);
}

function renderSuppliers(suppliers) {
    suppliersTableBody.replaceChildren();

    if (suppliers.length === 0) {
        showSuppliersMessage("No suppliers registered yet.");
        return;
    }

    for (const supplier of suppliers) {
        const row = document.createElement("tr");

        const values = [
            supplier.id,
            supplier.name,
            supplier.email,
            `${supplier.lead_time_days} days`
        ];

        for (const value of values) {
            const cell = document.createElement("td");
            cell.textContent = String(value ?? "—");
            row.appendChild(cell);
        }

        suppliersTableBody.appendChild(row);
    }
}

async function loadSuppliers() {
    refreshSuppliersButton.disabled = true;
    refreshSuppliersButton.textContent = "Loading...";

    showSuppliersMessage("Loading suppliers...");

    try {
        const response = await fetch("/suppliers", {
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(
                `Suppliers API returned HTTP ${response.status}`
            );
        }

        const suppliers = await response.json();

        if (!Array.isArray(suppliers)) {
            throw new Error("Unexpected suppliers response.");
        }

        renderSuppliers(suppliers);
    } catch (error) {
        console.error("Failed to load suppliers:", error);

        showSuppliersMessage(
            "Unable to load suppliers. Check the API connection."
        );
    } finally {
        refreshSuppliersButton.disabled = false;
        refreshSuppliersButton.textContent = "Refresh Suppliers";
    }
}

refreshSuppliersButton.addEventListener("click", loadSuppliers);

document.addEventListener("DOMContentLoaded", loadSuppliers);

const supplierForm = document.getElementById("supplier-form");
const createSupplierButton = document.getElementById(
    "create-supplier-button"
);
const supplierFormMessage = document.getElementById(
    "supplier-form-message"
);

async function createSupplier(event) {
    event.preventDefault();

    if (!supplierForm.reportValidity()) {
        return;
    }

    const name = document.getElementById(
        "supplier-name"
    ).value.trim();

    const email = document.getElementById(
        "supplier-email"
    ).value.trim();

    const leadTimeDays = Number(
        document.getElementById("supplier-lead-time").value
    );

    if (
        !name ||
        !email ||
        !Number.isInteger(leadTimeDays) ||
        leadTimeDays < 1 ||
        leadTimeDays > 365
    ) {
        supplierFormMessage.textContent =
            "Please enter valid supplier information.";
        return;
    }

    createSupplierButton.disabled = true;
    createSupplierButton.textContent = "Saving...";
    supplierFormMessage.textContent = "";

    try {
        const response = await fetch("/suppliers", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({
                name: name,
                email: email,
                lead_time_days: leadTimeDays
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(
                () => null
            );

            const detail = errorData?.detail;

            throw new Error(
                typeof detail === "string"
                    ? detail
                    : `Unable to create supplier (HTTP ${response.status}).`
            );
        }

        supplierForm.reset();

        supplierFormMessage.textContent =
            "Supplier created successfully.";

        await loadSuppliers();
await loadProductSuppliers();
    } catch (error) {
        console.error("Failed to create supplier:", error);

        supplierFormMessage.textContent = error.message;

    } finally {
        createSupplierButton.disabled = false;
        createSupplierButton.textContent = "Add Supplier";
    }
}

supplierForm.addEventListener("submit", createSupplier);

const productSupplierSelect = document.getElementById(
    "product-supplier"
);

async function loadProductSuppliers() {
    productSupplierSelect.replaceChildren();

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "No supplier";
    productSupplierSelect.appendChild(defaultOption);

    try {
        const response = await fetch("/suppliers", {
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(
                `Suppliers API returned HTTP ${response.status}`
            );
        }

        const suppliers = await response.json();

        if (!Array.isArray(suppliers)) {
            throw new Error("Unexpected suppliers response.");
        }

        for (const supplier of suppliers) {
            const option = document.createElement("option");

            option.value = String(supplier.id);
            option.textContent = supplier.name;

            productSupplierSelect.appendChild(option);
        }

    } catch (error) {
        console.error(
            "Failed to load product suppliers:",
            error
        );

        defaultOption.textContent = "Suppliers unavailable";
        productSupplierSelect.disabled = true;
        return;
    }

    productSupplierSelect.disabled = false;
}

document.addEventListener(
    "DOMContentLoaded",
    loadProductSuppliers
);

const productForm = document.getElementById("product-form");
const createProductButton = document.getElementById(
    "create-product-button"
);
const productFormMessage = document.getElementById(
    "product-form-message"
);

async function createProduct(event) {
    event.preventDefault();

    if (!productForm.reportValidity()) {
        return;
    }

    const sku = document.getElementById(
        "product-sku"
    ).value.trim();

    const name = document.getElementById(
        "product-name"
    ).value.trim();

    const price = document.getElementById(
        "product-price"
    ).value;

    const purchaseCost = document.getElementById(
        "product-purchase-cost"
    ).value;

    const stockQuantity = Number(
        document.getElementById("product-stock").value
    );

    const leadTimeDays = Number(
        document.getElementById("product-lead-time").value
    );

    const safetyStock = Number(
        document.getElementById("product-safety-stock").value
    );

    const supplierValue = productSupplierSelect.value;

    const validMoney = (value) =>
        /^\d+(\.\d{1,2})?$/.test(value);

    if (
        !sku ||
        !name ||
        !validMoney(price) ||
        (purchaseCost !== "" && !validMoney(purchaseCost)) ||
        !Number.isSafeInteger(stockQuantity) ||
        stockQuantity < 0 ||
        !Number.isSafeInteger(leadTimeDays) ||
        leadTimeDays < 1 ||
        leadTimeDays > 365 ||
        !Number.isSafeInteger(safetyStock) ||
        safetyStock < 0
    ) {
        productFormMessage.textContent =
            "Please enter valid product information.";
        return;
    }

    const supplierId = supplierValue === ""
        ? null
        : Number(supplierValue);

    if (
        supplierId !== null &&
        (!Number.isSafeInteger(supplierId) || supplierId <= 0)
    ) {
        productFormMessage.textContent =
            "Please select a valid supplier.";
        return;
    }

    const payload = {
        sku: sku,
        name: name,
        price: price,
        purchase_cost: purchaseCost === "" ? null : purchaseCost,
        stock_quantity: stockQuantity,
        lead_time_days: leadTimeDays,
        safety_stock: safetyStock,
        supplier_id: supplierId
    };

    createProductButton.disabled = true;
    createProductButton.textContent = "Saving...";
    productFormMessage.textContent = "";

    try {
        const response = await fetch("/products", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(
                () => null
            );

            const detail = errorData?.detail;

            throw new Error(
                typeof detail === "string"
                    ? detail
                    : `Unable to create product (HTTP ${response.status}).`
            );
        }

        productForm.reset();

        productFormMessage.textContent =
            "Product created successfully.";

        await loadProducts();
        await loadDashboardMetrics();

    } catch (error) {
        console.error("Failed to create product:", error);

        productFormMessage.textContent = error.message;

    } finally {
        createProductButton.disabled = false;
        createProductButton.textContent = "Add Product";
    }
}

productForm.addEventListener("submit", createProduct);
