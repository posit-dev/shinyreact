from pathlib import Path

import shinyreact
from data import calculate_metrics, filter_data, generate_sample_data
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive

# Generate sample data once when app starts
sample_data = generate_sample_data()

_src_dir = Path(__file__).parent
_dashboard_dep = HTMLDependency(
    name="dashboard",
    version=str(int((_src_dir / "dashboard.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "dashboard.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyreact.ui_output("main", extra_deps=[_dashboard_dep])


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------
def dashboard_app(*children: shinyreact.Node) -> shinyreact.Node:
    return shinyreact.Node(type="DashboardApp", children=list(children))


def filter_panel(
    date_range_id: str, search_id: str, categories_id: str
) -> shinyreact.Node:
    return shinyreact.Node(
        type="FilterPanel",
        props={
            "date_range_id": date_range_id,
            "search_id": search_id,
            "categories_id": categories_id,
        },
    )


def metrics_cards(output_id: str) -> shinyreact.Node:
    return shinyreact.Node(type="MetricsCards", props={"output_id": output_id})


def charts(output_id: str) -> shinyreact.Node:
    return shinyreact.Node(type="Charts", props={"output_id": output_id})


def data_table(output_id: str) -> shinyreact.Node:
    return shinyreact.Node(type="DataTable", props={"output_id": output_id})


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

    @shinyreact.reactive_output
    def main():
        return dashboard_app(
            filter_panel("date_range", "search_term", "selected_categories"),
            metrics_cards("metrics_data"),
            charts("chart_data"),
            data_table("table_data"),
        )

    @shinyreact.reactive_output
    def metrics_data():
        """Calculate and return metrics"""
        data = filtered_data()
        return calculate_metrics(data)

    @shinyreact.reactive_output
    def chart_data():
        """Return chart data in column-major format"""
        data = filtered_data()

        revenue_trend_columns = data["revenue_trend"].to_dict("list")
        category_performance_columns = data["category_performance"].to_dict("list")

        return {
            "revenue_trend": revenue_trend_columns,
            "category_performance": category_performance_columns,
        }

    @shinyreact.reactive_output
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
