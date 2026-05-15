"""End-to-end demo of shinyui's class-per-component hierarchy in ``with`` form.

This is the Express-with-blocks variant of ``14-unified-ui-prototype/``. The
two apps produce the same UI tree. Compare:

  - ``14-unified-ui-prototype/app.py`` — positional composition:
    ``card(accordion(accordion_panel("Settings", n_slider, ...), ...), ...)``
  - This file — context-manager composition:
    ``with card(): with accordion(): with accordion_panel("Settings"): ...``

Both rely on ``@expressify`` (Shiny Express's default for ``app.py``) so bare
expression statements get rewritten to ``sys.displayhook(...)`` calls. The
shinyui parent-tag context stack (issue #70) routes those values to the
innermost active ``with`` parent.

Renderers use the ``@<output>.render`` instance method instead of bare
``@render.code`` / ``@render.plot``. This binds the renderer to the output's
id (not the function's ``__name__``) and — because the decorator is an
assignment expression — does not trigger Express's displayhook auto-placement.
"""

from __future__ import annotations

import shinyui as su
from shiny import reactive
from shiny import ui as _sui
from shiny.express import ui

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
ui.page_opts(title="shinyui Stage A — with-block form")

# Build the UI tree with `with` blocks. Express's @expressify rewrite turns
# each bare expression below into `sys.displayhook(value)`; shinyui's parent
# stack routes them to the active `with` parent.
with su.card(id="main_card", full_screen=False) as main_card:
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
# ``@<output>.render`` binds the function to the output's id (not the
# function's __name__) and, being an assignment expression, does NOT trigger
# Express's displayhook auto-placement. No ``ui.hold()`` wrapper needed.


@summary_code.render
def _():
    return (
        f"n     = {n_slider.value()}\n"
        f"dist  = {dist_select.value()}\n"
        f"seed  = {seed_slider.value()}\n"
        f"open  = {acc.open_panels()}\n"
        f"fs    = {main_card.full_screen_value()}\n"
    )


@diag_code.render
def _():
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


# --- Reactive effects ------------------------------------------------------
@reactive.effect
@reactive.event(open_all_btn.clicked, ignore_init=True)
def _open_all_panels():
    acc.update(open=("Settings", "Diagnostics"))


@reactive.effect
@reactive.event(close_all_btn.clicked, ignore_init=True)
def _close_all_panels():
    acc.update(open=False)
