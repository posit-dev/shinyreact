from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def generate_sample_data(n_days: int = 365, n_products: int = 20) -> Dict[str, Any]:
    """Generate sample sales data.

    Returns two long-format frames keyed on date:
    - revenue_trend: one row per day with site-wide revenue/orders/users.
    - transactions: one row per (day, product) — the fact table the
      dashboard's MetricsCards / Charts (category) / DataTable cards all
      aggregate from inside ``filter_data``.

    Demonstrates the canonical Shiny pattern of a single shared
    ``@reactive.calc`` (``filtered_data``) deriving multiple outputs from
    one fact table, so a date-range change ripples through every card.
    """
    np.random.seed(42)  # For reproducible data

    # Date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=n_days - 1)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    # Product categories
    categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports"]
    products = [
        "Wireless Headphones",
        "Laptop Stand",
        "Smart Watch",
        "Bluetooth Speaker",
        "Phone Case",
        "Cotton T-Shirt",
        "Jeans",
        "Sneakers",
        "Wool Sweater",
        "Baseball Cap",
        "Programming Book",
        "Novel",
        "Cookbook",
        "Journal",
        "Art Supplies",
        "Garden Tools",
        "Kitchen Utensils",
        "Bedding Set",
        "Decorative Pillow",
        "Plant Pot",
    ]

    # Site-wide time series (orders/users aren't tracked per-product, so this
    # frame stays distinct from the transactions table below).
    revenue_base = (
        2000
        + 500 * np.sin(np.arange(len(dates)) * 0.3)
        + np.random.normal(0, 200, len(dates))
    )
    orders_base = (
        50
        + 20 * np.sin(np.arange(len(dates)) * 0.2)
        + np.random.poisson(10, len(dates))
    )
    users_base = (
        25
        + 15 * np.sin(np.arange(len(dates)) * 0.25)
        + np.random.poisson(5, len(dates))
    )

    revenue_trend = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "revenue": np.maximum(1000, revenue_base),
            "orders": np.maximum(10, orders_base),
            "users": np.maximum(5, users_base),
        }
    )

    # Per-product baseline: rates and metadata.
    product_baseline = pd.DataFrame(
        {
            "id": [f"prod_{i}" for i in range(1, n_products + 1)],
            "product": np.random.choice(products, n_products),
            "category": np.random.choice(categories, n_products),
            # Mean daily sales rate (units/day) — varies per product.
            "daily_sales_rate": np.random.uniform(0.5, 3.0, n_products),
            # Per-unit revenue ($/unit).
            "unit_revenue": np.round(np.random.uniform(20, 100, n_products), 2),
            # Static product attributes (independent of date).
            "growth": np.round(np.random.uniform(-15, 25, n_products), 1),
            "status": np.random.choice(
                ["active", "inactive", "low_stock"],
                n_products,
                p=[0.6, 0.2, 0.2],
            ),
        }
    )

    # Transaction log: one row per (date, product). With n_days=365 and
    # n_products=20, this is 7,300 rows — fine for a demo.
    n_dates = len(dates)
    daily_sales = np.random.poisson(
        product_baseline["daily_sales_rate"].to_numpy()[:, None],
        size=(n_products, n_dates),
    )
    daily_revenue = daily_sales * product_baseline["unit_revenue"].to_numpy()[:, None]

    transactions = pd.DataFrame(
        {
            "date": np.tile(dates.strftime("%Y-%m-%d").to_numpy(), n_products),
            "id": np.repeat(product_baseline["id"].to_numpy(), n_dates),
            "product": np.repeat(product_baseline["product"].to_numpy(), n_dates),
            "category": np.repeat(product_baseline["category"].to_numpy(), n_dates),
            "sales": daily_sales.reshape(-1).astype(int),
            "revenue": np.round(daily_revenue.reshape(-1), 2),
            "growth": np.repeat(product_baseline["growth"].to_numpy(), n_dates),
            "status": np.repeat(product_baseline["status"].to_numpy(), n_dates),
        }
    )

    return {
        "revenue_trend": revenue_trend,
        "transactions": transactions,
    }


def filter_data(
    data: Dict[str, Any],
    date_range: str = "last_30_days",
    search_term: str = "",
    selected_categories: List[str] = None,
) -> Dict[str, Any]:
    """Filter the fact tables by date / search / categories and return the
    aggregates each dashboard card needs.

    The transaction log is the single source of truth for products and
    category_performance — both are derived here, so any change to the
    date range, search, or category filter ripples to all three cards.
    """
    if selected_categories is None:
        selected_categories = []

    # Date window
    days_back = {
        "last_7_days": 7,
        "last_30_days": 30,
        "last_90_days": 90,
        "this_year": 365,
    }.get(date_range, 30)
    start_date = datetime.now().date() - timedelta(days=days_back - 1)

    # Site-wide time series for the top chart.
    revenue_trend = data["revenue_trend"].copy()
    revenue_trend["date_parsed"] = pd.to_datetime(revenue_trend["date"]).dt.date
    filtered_revenue = revenue_trend[revenue_trend["date_parsed"] >= start_date].drop(
        "date_parsed", axis=1
    )

    # Slice the transaction log by date.
    tx = data["transactions"].copy()
    tx["date_parsed"] = pd.to_datetime(tx["date"]).dt.date
    tx = tx[tx["date_parsed"] >= start_date].drop("date_parsed", axis=1)

    # Search term: matches against product name or category.
    if search_term:
        mask = tx["product"].str.contains(
            search_term, case=False, na=False
        ) | tx["category"].str.contains(search_term, case=False, na=False)
        tx = tx[mask]

    # Category checkboxes use lowercase keys; map them to the data labels.
    if selected_categories:
        category_map = {
            "electronics": "Electronics",
            "clothing": "Clothing",
            "books": "Books",
            "home": "Home & Garden",
            "sports": "Sports",
        }
        selected_labels = [
            category_map[c] for c in selected_categories if c in category_map
        ]
        if selected_labels:
            tx = tx[tx["category"].isin(selected_labels)]

    # Aggregate transactions → per-product rollup for the table card.
    if not tx.empty:
        filtered_products = (
            tx.groupby(
                ["id", "product", "category", "growth", "status"], as_index=False
            )
            .agg(sales=("sales", "sum"), revenue=("revenue", "sum"))
            .sort_values("revenue", ascending=False)
            .reset_index(drop=True)
        )
        filtered_category_performance = (
            filtered_products.groupby("category", as_index=False)
            .agg({"sales": "sum", "revenue": "sum"})
        )
    else:
        filtered_products = pd.DataFrame(
            columns=["id", "product", "category", "growth", "status", "sales", "revenue"]
        )
        filtered_category_performance = pd.DataFrame(
            columns=["category", "sales", "revenue"]
        )

    return {
        "revenue_trend": filtered_revenue,
        "products": filtered_products,
        "category_performance": filtered_category_performance,
    }


def calculate_metrics(
    current_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate metrics with comparison to previous period"""

    # Current metrics
    current_revenue = current_data["revenue_trend"]["revenue"].sum()
    current_users = current_data["revenue_trend"]["users"].sum()
    current_orders = current_data["revenue_trend"]["orders"].sum()
    current_conversion = (
        (current_orders / current_users * 100) if current_users > 0 else 0
    )

    # Previous metrics (mock calculation for demo)
    previous_revenue = current_revenue * 0.9
    previous_users = current_users * 0.85
    previous_orders = current_orders * 0.88
    previous_conversion = (
        (previous_orders / previous_users * 100) if previous_users > 0 else 0
    )

    # Calculate changes
    revenue_change = (
        ((current_revenue - previous_revenue) / previous_revenue * 100)
        if previous_revenue > 0
        else 0
    )
    users_change = (
        ((current_users - previous_users) / previous_users * 100)
        if previous_users > 0
        else 0
    )
    orders_change = (
        ((current_orders - previous_orders) / previous_orders * 100)
        if previous_orders > 0
        else 0
    )
    conversion_change = current_conversion - previous_conversion

    return {
        "revenue": {
            "title": "Total Revenue",
            "value": f"${int(current_revenue):,}",
            "change": round(revenue_change, 1),
            "trend": "up" if revenue_change >= 0 else "down",
        },
        "users": {
            "title": "New Users",
            "value": f"{int(current_users):,}",
            "change": round(users_change, 1),
            "trend": "up" if users_change >= 0 else "down",
        },
        "orders": {
            "title": "Orders",
            "value": f"{int(current_orders):,}",
            "change": round(orders_change, 1),
            "trend": "up" if orders_change >= 0 else "down",
        },
        "conversion": {
            "title": "Conversion Rate",
            "value": f"{current_conversion:.1f}%",
            "change": round(conversion_change, 1),
            "trend": "up" if conversion_change >= 0 else "down",
        },
    }
