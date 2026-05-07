from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shiny import reactive
from shiny.express import input, render
from shinyreact import reactive_output, set_page

matplotlib.use("Agg")

set_page()

sample_data = pd.DataFrame(
    {
        "id": range(1, 9),
        "age": [25, 30, 35, 28, 32, 27, 29, 33],
        "score": [85.5, 92.1, 88.3, 88.7, 95.2, 81.9, 87.4, 90.6],
    }
)


@reactive_output
def scatter_data():
    return sample_data[["age", "score"]].to_dict(orient="list")


@reactive_output
def processed_text():
    text = input.user_text() or ""
    if text == "":
        return ""
    return "".join(reversed(text.upper()))


@reactive_output
def text_length():
    return len(input.user_text() or "")


@render.text
def render_text_demo():
    text = input.user_text() or ""
    if text == "":
        return ""
    return f"render.text says: {text!r} ({len(text)} chars)"


@reactive_output
@reactive.event(input.button_trigger, ignore_init=True)
def button_response():
    now = datetime.now()
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    ms = now.microsecond // 1000
    return f"Event received at: {ts}.{ms:03d}"


@render.plot
def plot1():
    fig, ax = plt.subplots()
    ax.scatter(sample_data["age"], sample_data["score"], s=30, alpha=0.7)
    z = np.polyfit(sample_data["age"], sample_data["score"], 1)
    p = np.poly1d(z)
    x_trend = np.linspace(sample_data["age"].min(), sample_data["age"].max(), 100)
    ax.plot(x_trend, p(x_trend), "r--", linewidth=2, alpha=0.8)
    ax.set_xlabel("Age")
    ax.set_ylabel("Score")
    ax.set_title("Age vs Score")
    ax.grid(True, alpha=0.3)
    return fig
