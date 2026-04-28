from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shiny import reactive, render
from shinyjson import SpaApp, render_json

matplotlib.use("Agg")

sample_data = pd.DataFrame(
    {
        "id": range(1, 9),
        "age": [25, 30, 35, 28, 32, 27, 29, 33],
        "score": [85.5, 92.1, 88.3, 88.7, 95.2, 81.9, 87.4, 90.6],
    }
)


def server(input, output, session):  # noqa: ARG001
    @render_json
    def scatter_data():
        return sample_data[["age", "score"]].to_dict(orient="list")

    @render_json
    def processed_text():
        text = input.user_text() or ""
        if text == "":
            return ""
        return "".join(reversed(text.upper()))

    @render_json
    def text_length():
        return len(input.user_text() or "")

    @render_json
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


app = SpaApp(server)
