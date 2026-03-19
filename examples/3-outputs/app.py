from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, render

matplotlib.use("Agg")

mtcars = pd.read_csv(Path(__file__).parent / "mtcars.csv")

_outputs_dep = HTMLDependency(
    name="outputs-example",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "outputs.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("main", extra_deps=[_outputs_dep])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def main():
        return shinyjson.Spec(
            root="app",
            elements={
                "app": shinyjson.Element(type="App", props={}),
            },
        )

    @shinyjson.render
    def table_data():
        num_rows = input.table_rows()
        return mtcars.head(num_rows).to_dict(orient="list")

    @shinyjson.render
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
