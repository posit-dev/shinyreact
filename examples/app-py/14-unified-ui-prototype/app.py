"""End-to-end demo of shinyui's unified API — class-per-component hierarchy.

Exercises every reference class in one page:
  - input_slider, input_select, input_action_button  (inputs)
  - output_code                                      (output)
  - output_plot                                      (output with read-only signals)
  - card                                             (layout with state)
  - accordion + accordion_panel                      (layout + layout-as-child)

This is the Express variant of the demo. The same shinyui component classes
compose both positionally (``card(accordion(...), ...)``) and via ``with``
blocks (``with card(): with accordion(): ...``). This file uses the ``with``-
block form as the idiomatic Express style; the two approaches produce
identical UI trees. See issue #70 for context.

In Express the script runs once per session — ``get_current_session()`` is
bound while the module's top-level statements execute, so components register
themselves on the session at construction time. shinyui's parent-tag context
stack (issue #70) routes bare expression statements inside a ``with`` block
to the innermost active parent.
"""

from __future__ import annotations

import shinyui as su
from shiny import reactive
from shiny import ui as _sui
from shiny.express import render, ui

# --- Components -------------------------------------------------------------
# Components without children are constructed at module top-level so the
# server-side accessors (``n_slider.value()``, etc.) bind to instances we hold.
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

# --- Page ------------------------------------------------------------------
ui.page_opts(title="shinyui Stage A prototype")

# Build the UI tree with `with` blocks. Express's @expressify rewrite turns
# each bare expression below into `sys.displayhook(value)`; shinyui's parent
# stack routes them to the active `with` parent.
with su.card(id="main_card", full_screen=False) as main_card:
    # Use plain shiny.ui.layout_column_wrap here, not shiny.express.ui's
    # recall-context-managed version (the express one takes 0 positional args).
    _sui.layout_column_wrap(open_all_btn, close_all_btn, width=1 / 2)
    with su.accordion(id="acc", open="Settings") as acc:
        with su.accordion_panel("Settings"):
            n_slider
            dist_select
            seed_slider
        with su.accordion_panel("Diagnostics"):
            summary_code
            diag_code
    plot_handle


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
