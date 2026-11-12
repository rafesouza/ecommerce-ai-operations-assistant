
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
