from pathlib import Path

import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive

from data import generate_sample_data, filter_data, calculate_metrics

# Generate sample data once when app starts
sample_data = generate_sample_data()

_dashboard_dep = HTMLDependency(
    name="dashboard",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "dashboard.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("main", extra_deps=[_dashboard_dep])


def server(input: Inputs, output: Outputs, session: Session):

    @reactive.calc
    def filtered_data():
        """Reactive data filtering"""
        date_range = (
            input.date_range() if input.date_range() is not None else "last_30_days"
        )
        search_term = input.search_term() if input.search_term() is not None else ""
        selected_categories = (
            input.selected_categories()
            if input.selected_categories() is not None
            else []
        )

        return filter_data(
            sample_data,
            date_range=date_range,
            search_term=search_term,
            selected_categories=selected_categories,
        )

    @shinyjson.render
    def main():
        return shinyjson.Spec(
            root="app",
            elements={
                "app": shinyjson.Element(type="App", props={}),
            },
        )

    @shinyjson.render
    def metrics_data():
        """Calculate and return metrics"""
        data = filtered_data()
        return calculate_metrics(data)

    @shinyjson.render
    def chart_data():
        """Return chart data in column-major format"""
        data = filtered_data()

        revenue_trend_columns = data["revenue_trend"].to_dict("list")
        category_performance_columns = data["category_performance"].to_dict("list")

        return {
            "revenue_trend": revenue_trend_columns,
            "category_performance": category_performance_columns,
        }

    @shinyjson.render
    def table_data():
        """Return table data in column-major format"""
        data = filtered_data()

        products = data["products"].copy()
        if len(products) > 0:
            products_sorted = products.sort_values("revenue", ascending=False)
            top_products = products_sorted.head(10)
            columns_data = top_products.to_dict("list")
        else:
            columns_data = {
                "id": [],
                "product": [],
                "category": [],
                "sales": [],
                "revenue": [],
                "growth": [],
                "status": [],
            }

        return {"columns": columns_data, "total_rows": len(data["products"])}


app = App(app_ui, server)
