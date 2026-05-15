"""End-to-end demo of shinyui's class-per-component hierarchy in **Shiny Core**.

This is the Core (positional composition) variant. Its sibling
``15-shinyui-with-blocks/app.py`` builds the same UI tree in Shiny Express
using ``with``-blocks. Together they demonstrate the unified API from
issue #70: a single set of ``shinyui`` classes that work in both idioms.

  - **This file** (Core): ``app_ui = ui.page_fluid(card(accordion(panel(...))))``
    plus a ``server(input, output, session)`` function.
  - **Example 15** (Express): ``with card(): with accordion(): with panel(): ...``
    plus ``@render.*`` and ``@reactive.effect`` at the module top level.

The same component classes (``card``, ``accordion``, ``accordion_panel``,
``input_slider``, etc.) compose identically in both modes. The server-side
accessors (``slider.value()``, ``acc.update(...)``, ``card.full_screen_value()``)
work the same in both — they resolve the active session at call time, so
they are safe to define at module load in Core and access from inside the
``server`` function.
"""

from __future__ import annotations

import shinyui as su
from shiny import App, Inputs, Outputs, Session, reactive
from shiny import ui as _sui

# --- Components -------------------------------------------------------------
# Build all shinyui components at module top-level so the server function
# can reference them by handle. Construction does not require a session.
n_slider = su.input_slider("n", "Sample size", 10, 1000, 100)
seed_slider = su.input_slider("seed", "Seed", 1, 1000, 42)
dist_select = su.input_select(
    "dist",
    "Distribution",
    {"normal": "Normal", "uniform": "Uniform"},
)
plot_handle = su.output_plot("plot", click=True, brush=True)
open_all_btn = su.input_action_button("open_all", "Open all panels")
close_all_btn = su.input_action_button("close_all", "Close all panels")
summary_code = su.output_code("summary")
diag_code = su.output_code("diag")

acc = su.accordion(
    su.accordion_panel("Settings", n_slider, dist_select, seed_slider),
    su.accordion_panel("Diagnostics", summary_code, diag_code),
    id="acc",
    open="Settings",
)
main_card = su.card(
    _sui.layout_column_wrap(open_all_btn, close_all_btn, width=1 / 2),
    acc,
    plot_handle,
    id="main_card",
    full_screen=False,
)

# --- UI ---------------------------------------------------------------------
app_ui = _sui.page_fluid(
    main_card,
    title="shinyui Stage A — Core (positional) form",
)


# --- Server -----------------------------------------------------------------
def server(input: Inputs, output: Outputs, session: Session) -> None:
    @summary_code.render
    def _() -> str:
        return (
            f"n     = {n_slider.value()}\n"
            f"dist  = {dist_select.value()}\n"
            f"seed  = {seed_slider.value()}\n"
            f"open  = {acc.open_panels()}\n"
            f"fs    = {main_card.full_screen_value()}\n"
        )

    @diag_code.render
    def _() -> str:
        return (
            f"click = {plot_handle.click_value()}\n"
            f"brush = {plot_handle.brush_value()}\n"
        )

    @plot_handle.render
    def _():
        import matplotlib.pyplot as plt
        import numpy as np

        rng = np.random.default_rng(seed_slider.value())
        n = n_slider.value()
        if dist_select.value() == "normal":
            x = rng.standard_normal(n)
            y = rng.standard_normal(n)
        else:
            x = rng.uniform(-2, 2, n)
            y = rng.uniform(-2, 2, n)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(x, y, s=12, alpha=0.6)
        ax.set_title(f"{dist_select.value()} sample, n={n}, seed={seed_slider.value()}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, alpha=0.3)
        return fig

    @reactive.effect
    @reactive.event(open_all_btn.clicked, ignore_init=True)
    def _open_all_panels():
        acc.update(open=("Settings", "Diagnostics"))

    @reactive.effect
    @reactive.event(close_all_btn.clicked, ignore_init=True)
    def _close_all_panels():
        acc.update(open=False)


app = App(app_ui, server)
