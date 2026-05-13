"""End-to-end demo of shinyui's class-per-component hierarchy (Shiny Express).

Exercises every reference class in one page:
  - UiInputSlider, UiInputSelect, UiInputActionButton  (inputs)
  - UiOutputCode                                       (output)
  - UiOutputPlot                                       (output with read-only signals)
  - UiCard                                             (layout with state)
  - UiAccordion + UiAccordionPanel                     (layout + layout-as-child)

This is the Express variant of the demo. In Express the script runs once per
session — ``get_current_session()`` is bound while the module's top-level
statements execute, so the components register themselves on the session at
construction time. shinyui containers are still built programmatically (passing
children to the factories) because the parent-tag stack / ``with`` integration
is umbrella sub-issue 3, deferred from this prototype.
"""

from __future__ import annotations

import shinyui as su
from shiny import reactive
from shiny import ui as _sui
from shiny.express import render, ui

# --- Components -------------------------------------------------------------
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
acc = su.accordion(
    su.accordion_panel("Settings", n_slider, dist_select, seed_slider),
    su.accordion_panel(
        "Diagnostics",
        su.output_code("summary"),
        su.output_code("diag"),
    ),
    id="acc",
    open="Settings",
)
main_card = su.card(
    # Use plain shiny.ui.layout_column_wrap here, not shiny.express.ui's
    # recall-context-managed version (the express one takes 0 positional args).
    _sui.layout_column_wrap(open_all_btn, close_all_btn, width=1 / 2),
    acc,
    plot_handle,
    id="main_card",
    full_screen=False,
)

# --- Page ------------------------------------------------------------------
ui.page_opts(title="shinyui Stage A prototype")

# Top-level expression: Express's `@expressify`-driven runtime appends the
# value to the current page container. shinyui factories are NOT Express-aware,
# so we hand the constructed instance to Express via this expression statement.
main_card


# --- Renderers -------------------------------------------------------------
# `ui.hold()` suppresses Express's default auto-placement so each renderer
# binds to its id-matching output element that we placed inside the
# accordion / card above. Without `hold()`, Express would insert a SECOND
# `<pre id="summary">` at the page tail, duplicating the id and breaking
# the in-place output binding.
with ui.hold():

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


# --- Reactive effects ------------------------------------------------------
@reactive.effect
@reactive.event(open_all_btn.clicked, ignore_init=True)
def _open_all_panels():
    acc.update(open=("Settings", "Diagnostics"))


@reactive.effect
@reactive.event(close_all_btn.clicked, ignore_init=True)
def _close_all_panels():
    # update_accordion's `show=` takes a panel value list, OR True/False.
    # False closes all panels in the set.
    acc.update(open=False)
