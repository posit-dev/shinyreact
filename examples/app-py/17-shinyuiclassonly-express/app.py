# End-to-end demo of shinyuiclassonly's class hierarchy in `with` form.
#
# Express variant of `16-shinyuiclassonly-core/`. Both apps produce the same
# UI tree. Compared with example 15 (the ``shinyui`` ``with``-block demo):
#
#   - imports ``shinyuiclassonly as su`` instead of ``shinyui as su``
#   - no walrus operators: the server reads inputs via ``input.<id>()``
#     directly, so there is no reason to bind a module-level name on any
#     component instance.
#   - reads use ``input.<id>()`` instead of ``n_slider.value()`` etc.
#   - updates use ``shiny.ui.update_accordion(...)`` instead of
#     ``acc.update(...)``.
#   - the plot renderer (``shinyuiclassonly.render_plot``) still carries
#     the interaction flags and auto-places its ``output_plot``; it just
#     no longer carries ``.click_value`` / ``.brush_value`` accessors.
#
# Both rely on ``@expressify`` (Shiny Express's default for ``app.py``) so
# bare expression statements get rewritten to ``sys.displayhook(...)``
# calls. The shinyuiclassonly parent-tag context stack routes those values
# to the innermost active ``with`` parent.
#
# A module-level docstring would render as raw text on the page because
# ``@expressify`` wraps every bare-expression statement (including the
# docstring) in ``sys.displayhook(...)``. So this module uses a comment
# block instead.

from __future__ import annotations

import shinyuiclassonly as su
from shiny import reactive, render
from shiny import ui as _sui
from shiny.express import input, ui

# --- Page ------------------------------------------------------------------
ui.page_opts(title="shinyuiclassonly — Express with-blocks")

ui.markdown(
    """
    ### shinyuiclassonly — Express with-blocks

    Express variant of `16-shinyuiclassonly-core/`. Same components, same
    tree, expressed as `with card(): with accordion(): ...`. The server
    reads inputs via `input.<id>()` directly — no walrus bindings needed.
    """
)

with su.card(id="main_card", full_screen=False):
    _sui.layout_column_wrap(
        su.input_action_button("open_all", "Open all panels"),
        su.input_action_button("close_all", "Close all panels"),
        width=1 / 2,
    )
    with su.accordion(id="acc", open="Settings"):
        with su.accordion_panel("Settings"):
            su.input_slider("n", "Sample size", 10, 1000, 100)
            su.input_select(
                "dist",
                "Distribution",
                {"normal": "Normal", "uniform": "Uniform"},
            )
            su.input_slider("seed", "Seed", 1, 1000, 42)
        with su.accordion_panel("Diagnostics"):

            @render.code
            def summary():
                return (
                    f"n     = {input.n()}\n"
                    f"dist  = {input.dist()}\n"
                    f"seed  = {input.seed()}\n"
                    f"open  = {tuple(input.acc() or ())}\n"
                    f"fs    = {bool(input.main_card_full_screen())}\n"
                )

            @render.code
            def diag():
                return (
                    f"click = {input.plot_click()}\n"
                    f"brush = {input.plot_brush()}\n"
                )

    @su.render_plot(click=True, brush=True)
    def plot():
        import matplotlib.pyplot as plt
        import numpy as np

        rng = np.random.default_rng(input.seed())
        n = input.n()
        if input.dist() == "normal":
            x = rng.standard_normal(n)
            y = rng.standard_normal(n)
        else:
            x = rng.uniform(-2, 2, n)
            y = rng.uniform(-2, 2, n)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(x, y, s=12, alpha=0.6)
        ax.set_title(f"{input.dist()} sample, n={n}, seed={input.seed()}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, alpha=0.3)
        return fig


# --- Reactive effects ------------------------------------------------------
@reactive.effect
@reactive.event(input.open_all, ignore_init=True)
def _open_all_panels():
    _sui.update_accordion("acc", show=["Settings", "Diagnostics"])


@reactive.effect
@reactive.event(input.close_all, ignore_init=True)
def _close_all_panels():
    _sui.update_accordion("acc", show=False)
