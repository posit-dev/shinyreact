from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive, render

matplotlib.use("Agg")

# Generate sample data
sample_data = pd.DataFrame(
    {
        "id": range(1, 9),
        "age": [25, 30, 35, 28, 32, 27, 29, 33],
        "score": [85.5, 92.1, 88.3, 88.7, 95.2, 81.9, 87.4, 90.6],
        "category": ["A", "B", "A", "C", "B", "A", "C", "B"],
    }
)

_shadcn_dep = HTMLDependency(
    name="shadcn-example",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "shadcn.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("main", extra_deps=[_shadcn_dep])


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
    def processed_text():
        text = input.user_text() if input.user_text() is not None else ""
        if text == "":
            return ""
        # Simple text processing - uppercase and reverse
        return "".join(reversed(text.upper()))

    @shinyjson.render
    def text_length():
        text = input.user_text() if input.user_text() is not None else ""
        return str(len(text))

    @shinyjson.render
    @reactive.event(input.button_trigger, ignore_init=True)
    def button_response():
        now = datetime.now()
        return f"Event received at: {now.strftime('%Y-%m-%d %H:%M:%S')}.{now.microsecond // 10000:02d}"

    @render.plot()
    def plot1():
        fig, ax = plt.subplots()

        ax.scatter(sample_data["age"], sample_data["score"], s=30, alpha=0.7)

        # Add trend line
        z = np.polyfit(sample_data["age"], sample_data["score"], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(sample_data["age"].min(), sample_data["age"].max(), 100)
        ax.plot(x_trend, p(x_trend), "r--", linewidth=2, alpha=0.8)

        ax.set_xlabel("Age")
        ax.set_ylabel("Score")
        ax.set_title("Age vs Score")
        ax.grid(True, alpha=0.3)

        return fig


app = App(app_ui, server)
