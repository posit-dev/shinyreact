from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shinyreact
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, render

matplotlib.use("Agg")

mtcars = pd.read_csv(Path(__file__).parent / "mtcars.csv")

_src_dir = Path(__file__).parent
_outputs_dep = HTMLDependency(
    name="outputs-example",
    version=str(int((_src_dir / "outputs.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "outputs.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyreact.output_react("main", extra_deps=[_outputs_dep])


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------
def page_layout(title: str, *children: shinyreact.Node) -> shinyreact.Node:
    return shinyreact.Node(
        type="PageLayout", props={"title": title}, children=list(children)
    )


def slider_card(input_id: str, default_value: int = 4) -> shinyreact.Node:
    return shinyreact.Node(
        type="SliderCard",
        props={"input_id": input_id, "default_value": default_value},
    )


def statistics_card(output_id: str) -> shinyreact.Node:
    return shinyreact.Node(type="StatisticsCard", props={"output_id": output_id})


def data_table_card(output_id: str) -> shinyreact.Node:
    return shinyreact.Node(type="DataTableCard", props={"output_id": output_id})


def plot_card(plot_id: str) -> shinyreact.Node:
    return shinyreact.Node(type="PlotCard", props={"plot_id": plot_id})


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.render_react
    def main():
        return page_layout(
            "Shiny React Output Examples",
            slider_card("table_rows"),
            statistics_card("table_stats"),
            data_table_card("table_data"),
            plot_card("plot1"),
        )

    @shinyreact.reactive_output
    def table_data():
        num_rows = input.table_rows()
        return mtcars.head(num_rows).to_dict(orient="list")

    @shinyreact.reactive_output
    def table_stats():
        num_rows = input.table_rows()
        mtcars_subset = mtcars.head(num_rows)

        return {
            "colname": "mpg",
            "mean": float(mtcars_subset["mpg"].mean()),
            "median": float(mtcars_subset["mpg"].median()),
            "min": float(mtcars_subset["mpg"].min()),
            "max": float(mtcars_subset["mpg"].max()),
        }

    @render.plot()
    def plot1():
        num_rows = input.table_rows()
        mtcars_subset = mtcars.head(num_rows)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(
            mtcars_subset["wt"],
            mtcars_subset["mpg"],
            color="steelblue",
            alpha=0.7,
            s=60,
        )

        z = np.polyfit(mtcars_subset["wt"], mtcars_subset["mpg"], 1)
        p = np.poly1d(z)
        ax.plot(
            mtcars_subset["wt"],
            p(mtcars_subset["wt"]),
            "r--",
            alpha=0.8,
            linewidth=2,
        )

        ax.set_xlabel("Weight (1000 lbs)")
        ax.set_ylabel("Miles per Gallon")
        ax.set_title(f"MPG vs Weight - {len(mtcars_subset)} cars")
        ax.grid(True, alpha=0.3)

        return fig


app = App(app_ui, server)
