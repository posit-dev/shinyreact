"""End-to-end demo of shinyui's class-per-component hierarchy.

Exercises every reference class in one page:
  - UiInputSlider, UiInputSelect    (simple + structured inputs)
  - UiOutputCode                    (output)
  - UiOutputPlot                    (output with read-only signals)
  - UiCard                          (layout with state)
  - UiAccordion + UiAccordionPanel  (layout-with-state + layout-as-child)

Components are constructed at module level. In Shiny Core, ``app_ui(request)``
runs during the HTTP phase — before any WebSocket session exists — so a
session-time id→instance registry would be empty when ``server()`` later runs.
Module-level construction sidesteps that timing issue: ``app_ui`` and
``server`` share the same instances via closure. The per-session bookmark
serializer registry is therefore a no-op in this example; the class accessors
(``.value()``, ``.full_screen_value()``, ``.open_panels()``, ``.click_value()``,
``.brush_value()``) and ``.update(...)`` work because ``_require_session``
falls back to ``get_current_session()`` at call time, which is bound while
``server()`` runs.
"""

from __future__ import annotations

import shinyui as su
from shiny import App, Inputs, Outputs, Session, reactive, render, ui

# --- Components -------------------------------------------------------------
n_slider = su.input_slider("n", "Sample size", 10, 1000, 100)
seed_slider = su.input_slider("seed", "Seed", 1, 1000, 42)
dist_select = su.input_select(
    "dist",
    "Distribution",
    {"normal": "Normal", "uniform": "Uniform"},
)
plot_handle = su.output_plot("plot", click=True, brush=True)
acc = su.accordion(
    su.accordion_panel("Settings", n_slider, dist_select, seed_slider),
    su.accordion_panel("Diagnostics", su.output_code("diag")),
    id="acc",
    open="Settings",
)
main_card = su.card(
    ui.layout_column_wrap(
        ui.input_action_button("open_all", "Open all panels"),
        ui.input_action_button("close_all", "Close all panels"),
        width=1 / 2,
    ),
    acc,
    su.output_code("summary"),
    plot_handle,
    id="main_card",
    full_screen=False,
)


def app_ui(request):
    return ui.page_fluid(main_card, title="shinyui Stage A prototype")


def server(input: Inputs, output: Outputs, session: Session):
    @render.code
    def summary():
        # Reads via class accessors — no `input.n()` / `input.dist()` needed.
        return (
            f"n     = {n_slider.value()}\n"
            f"dist  = {dist_select.value()}\n"
            f"seed  = {seed_slider.value()}\n"
            f"open  = {acc.open_panels()}\n"
            f"fs    = {main_card.full_screen_value()}\n"
        )

    @render.code
    def diag():
        return (
            f"click = {plot_handle.click_value()}\n"
            f"brush = {plot_handle.brush_value()}\n"
        )

    @render.plot
    def plot():
        # Real scatter plot driven by the slider/select/seed inputs.
        # Demonstrates the read-accessor chain ending in @render.plot:
        # all three reads establish reactive deps so the plot recomputes
        # on input changes.
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

    # Server-driven .update() on the layout-with-state accordion.
    # Each button click is an event input (action button → counter); we use
    # @reactive.event so a click runs the effect exactly once, not on every
    # other input change.
    @reactive.effect
    @reactive.event(input.open_all, ignore_init=True)
    def _open_all_panels():
        acc.update(open=("Settings", "Diagnostics"))

    @reactive.effect
    @reactive.event(input.close_all, ignore_init=True)
    def _close_all_panels():
        # update_accordion's `show=` takes a panel value list, OR True/False.
        # False closes all panels in the set.
        acc.update(open=False)


app = App(app_ui, server)
