
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
