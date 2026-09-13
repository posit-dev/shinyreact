import subprocess
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shiny import reactive
from shiny.express import input, render
from shinyreact import reactive_output, set_react_page

matplotlib.use("Agg")

# The Vite bundle is gitignored, so a fresh clone has no `www/` at all and
# Shiny fails to mount it. Build it on first run instead of greeting the
# reader with a stack trace.
_app_dir = Path(__file__).parent
if not (_app_dir / "www" / "ui.js").exists():
    print("www/ui.js not found -- building the client bundle...", file=sys.stderr)
    subprocess.run(["npm", "install"], cwd=_app_dir, check=True)
    subprocess.run(["npm", "run", "build"], cwd=_app_dir, check=True)

set_react_page()

sample_data = pd.DataFrame(
    {
        "id": range(1, 9),
        "age": [25, 30, 35, 28, 32, 27, 29, 33],
        "score": [85.5, 92.1, 88.3, 88.7, 95.2, 81.9, 87.4, 90.6],
    }
)


@reactive_output
def scatter_data():
    # `.loc[:, [...]]`, not `[[...]]`: pandas types the latter as
    # `Series | Unknown`, and `Series.to_dict()` takes no `orient=`.
    return sample_data.loc[:, ["age", "score"]].to_dict(orient="list")


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
