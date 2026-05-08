from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shinyreact
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive, render

# Create mtcars equivalent dataset
mtcars = pd.DataFrame(
    {
        "mpg": [21.0, 21.0, 22.8, 21.4, 18.7, 18.1, 14.3, 24.4, 22.8, 19.2],
        "cyl": [6, 6, 4, 6, 8, 6, 8, 4, 4, 6],
        "disp": [
            160.0,
            160.0,
            108.0,
            258.0,
            360.0,
            225.0,
            360.0,
            146.7,
            140.8,
            167.6,
        ],
        "hp": [110, 110, 93, 110, 175, 105, 245, 62, 95, 123],
        "drat": [3.90, 3.90, 3.85, 3.08, 3.15, 2.76, 3.21, 3.69, 3.92, 3.92],
    }
)
mtcars.index = [
    "Mazda RX4",
    "Mazda RX4 Wag",
    "Datsun 710",
    "Hornet 4 Drive",
    "Hornet Sportabout",
    "Valiant",
    "Duster 360",
    "Merc 240D",
    "Merc 230",
    "Merc 280",
]

_src_dir = Path(__file__).parent
_blended_dep = HTMLDependency(
    name="blended-example",
    version=str(int((_src_dir / "blended.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "blended.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyreact.ui_output("main", extra_deps=[_blended_dep])


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------
def sidebar_app(title: str, *children: shinyreact.Node) -> shinyreact.Node:
    return shinyreact.Node(
        type="SidebarApp", props={"title": title}, children=list(children)
    )


def dashboard_panel(
    months_id: str, region_id: str, sales_plot_id: str
) -> shinyreact.Node:
    return shinyreact.Node(
        type="DashboardPanel",
        props={
            "months_id": months_id,
            "region_id": region_id,
            "sales_plot_id": sales_plot_id,
        },
    )


def data_panel(
    data_table_id: str, refresh_id: str, refresh_count_id: str
) -> shinyreact.Node:
    return shinyreact.Node(
        type="DataPanel",
        props={
            "data_table_id": data_table_id,
            "refresh_id": refresh_id,
            "refresh_count_id": refresh_count_id,
        },
    )


def settings_panel(
    username_id: str,
    dark_mode_id: str,
    notifications_id: str,
    settings_output_id: str,
) -> shinyreact.Node:
    return shinyreact.Node(
        type="SettingsPanel",
        props={
            "username_id": username_id,
            "dark_mode_id": dark_mode_id,
            "notifications_id": notifications_id,
            "settings_output_id": settings_output_id,
        },
    )


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        return sidebar_app(
            "Blended Demo",
            dashboard_panel("months", "region", "salesPlot"),
            data_panel("dataTable", "refresh", "refreshCount"),
            settings_panel("username", "darkMode", "notifications", "currentSettings"),
        )

    # Sales Plot - reactive to months and region
    @render.plot
    def salesPlot():
        months = np.arange(1, input.months() + 1)
        np.random.seed(42)
        sales = np.cumsum(np.random.uniform(50, 150, input.months()))

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(
            months,
            sales,
            linewidth=2,
            color="#2563eb",
            marker="o",
            markersize=8,
            markerfacecolor="#2563eb",
        )
        ax.set_title(f"Sales Trend - {input.region()}", fontsize=14, fontweight="bold")
        ax.set_xlabel("Month", fontsize=11)
        ax.set_ylabel("Cumulative Sales ($1000s)", fontsize=11)
        ax.grid(True, color="#e5e7eb", linestyle="-", linewidth=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        return fig

    # Data Table - rendered as JSON for useShinyOutputValue
    @shinyreact.reactive_output
    def dataTable():
        return {
            "columns": list(mtcars.columns),
            "rows": [
                {"name": name, "values": list(row)}
                for name, row in zip(mtcars.index, mtcars.values.tolist())
            ],
        }

    # Refresh Counter
    refresh_count = reactive.value(0)

    @reactive.effect
    @reactive.event(input.refresh)
    def _():
        refresh_count.set(refresh_count() + 1)

    @shinyreact.reactive_output
    def refreshCount():
        return f"Data refreshed {refresh_count()} times"

    # Current Settings Display
    @shinyreact.reactive_output
    def currentSettings():
        username = input.username() if len(input.username()) > 0 else "(not set)"
        dark = input.darkMode()
        notif = input.notifications()
        return f"username: {username}\ndarkMode: {dark}\nnotifications: {notif}"


app = App(app_ui, server)
