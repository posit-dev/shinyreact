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

_src_dir = Path(__file__).parent
_shadcn_dep = HTMLDependency(
    name="shadcn-example",
    version=str(int((_src_dir / "shadcn.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "shadcn.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("main", extra_deps=[_shadcn_dep])


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------
def page_layout(title: str, subtitle: str, *children: shinyjson.Node) -> shinyjson.Node:
    return shinyjson.Node(
        type="PageLayout",
        props={"title": title, "subtitle": subtitle},
        children=list(children),
    )


def grid(*children: shinyjson.Node) -> shinyjson.Node:
    return shinyjson.Node(type="Grid", children=list(children))


def text_input_card(
    input_id: str, processed_output_id: str, length_output_id: str
) -> shinyjson.Node:
    return shinyjson.Node(
        type="TextInputCard",
        props={
            "input_id": input_id,
            "processed_output_id": processed_output_id,
            "length_output_id": length_output_id,
        },
    )


def button_event_card(input_id: str, output_id: str) -> shinyjson.Node:
    return shinyjson.Node(
        type="ButtonEventCard",
        props={"input_id": input_id, "output_id": output_id},
    )


def plot_card(plot_id: str) -> shinyjson.Node:
    return shinyjson.Node(type="PlotCard", props={"plot_id": plot_id})


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def main():
        return page_layout(
            "Shiny + React + shadcn/ui",
            "Demonstrating shadcn/ui components with various shiny-react output types",
            grid(
                text_input_card("user_text", "processed_text", "text_length"),
                button_event_card("button_trigger", "button_response"),
            ),
            grid(plot_card("plot1")),
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
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        ms = now.microsecond // 10000
        return f"Event received at: {ts}.{ms:02d}"

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
