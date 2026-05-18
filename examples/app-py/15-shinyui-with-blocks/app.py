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

Renderer ``def`` statements are placed at module top level (outside any
``with`` block) so Express's expressify hook auto-displays them. The plot
renderer is :class:`shinyui.render_plot`, which auto-places its placeholder
with the right interaction flags via ``auto_output_ui()`` and owns the
``click_value`` / ``brush_value`` / ``hover_value`` / ``dbl_value``
accessors.
"""

from __future__ import annotations

import shinyui as su
from shiny import reactive, render
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


# --- Renderers -------------------------------------------------------------
# Renderer ``def`` statements live at the module top level; Express's
# expressify hook (``_expressify_decorator_function_def``) auto-displays them
# because each returned Renderer has ``_repr_html_``. The text renderers
# match the ``output_code`` placeholders above by name; the plot renderer
# (``shinyui.render_plot``) auto-places its own placeholder.


@render.code
def summary():
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
        f"click = {plot.click_value()}\n"
        f"brush = {plot.brush_value()}\n"
    )


@su.render_plot(click=True, brush=True)
def plot():
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
@reactive.event(open_all_btn.value, ignore_init=True)
def _open_all_panels():
    acc.update(open=("Settings", "Diagnostics"))


@reactive.effect
@reactive.event(close_all_btn.value, ignore_init=True)
def _close_all_panels():
    acc.update(open=False)
