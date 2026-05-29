"""End-to-end demo of shinyuiclassonly's class hierarchy in **Shiny Core**.

This is the Core (positional composition) variant. Its sibling
``17-shinyuiclassonly-express/app.py`` builds the same UI tree in Shiny
Express using ``with``-blocks.

Compared with examples 14 / 15 (the ``shinyui`` versions of this app):

  - The same component classes (``card``, ``accordion``,
    ``accordion_panel``, ``input_slider``, …) are imported, but from
    ``shinyuiclassonly`` instead of ``shinyui``.
  - No walrus operators on inputs or layouts. The server reads inputs via
    ``input.<id>()`` directly, so there is no reason to bind a
    module-level name on any component instance.
  - Reads use ``input.<id>()`` instead of ``n_slider.value()`` /
    ``acc.open_panels()`` / ``main_card.value_full_screen()`` /
    ``plot.value_click()``.
  - Updates use ``shiny.ui.update_accordion(...)`` directly instead of
    ``acc.update(...)``.
  - The plot renderer (``shinyuiclassonly.render_plot``) still carries
    the interaction flags and auto-places its ``output_plot``; it just
    no longer carries ``.value_click`` / ``.value_brush`` accessors.

The architectural delta between this file and example 14 is the cost of
the session-bound machinery that ``shinyui`` adds on top of the class
hierarchy.
"""

from __future__ import annotations

import shinyuiclassonly as su
from shiny import App, Inputs, Outputs, Session, reactive, render
from shiny import ui as _sui

# --- UI ---------------------------------------------------------------------
app_ui = _sui.page_fluid(
    su.card(
        _sui.layout_column_wrap(
            su.input_action_button("open_all", "Open all panels"),
            su.input_action_button("close_all", "Close all panels"),
            width=1 / 2,
        ),
        su.accordion(
            su.accordion_panel(
                "Settings",
                su.input_slider("n", "Sample size", 10, 1000, 100),
                su.input_select(
                    "dist",
                    "Distribution",
                    {"normal": "Normal", "uniform": "Uniform"},
                ),
                su.input_slider("seed", "Seed", 1, 1000, 42),
            ),
            su.accordion_panel(
                "Diagnostics",
                su.output_code("summary"),
                su.output_code("diag"),
            ),
            id="acc",
            open="Settings",
        ),
        su.output_plot("plot", click=True, brush=True),
        id="main_card",
        full_screen=False,
    ),
    title="shinyuiclassonly — Core (positional) form",
)


# --- Server -----------------------------------------------------------------
def server(input: Inputs, output: Outputs, session: Session) -> None:
    @render.code
    def summary() -> str:
        return (
            f"n     = {input.n()}\n"
            f"dist  = {input.dist()}\n"
            f"seed  = {input.seed()}\n"
            f"open  = {tuple(input.acc() or ())}\n"
            f"fs    = {bool(input.main_card_full_screen())}\n"
        )

    @render.code
    def diag() -> str:
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

    @reactive.effect
    @reactive.event(input.open_all, ignore_init=True)
    def _open_all_panels():
        _sui.update_accordion("acc", show=["Settings", "Diagnostics"], session=session)

    @reactive.effect
    @reactive.event(input.close_all, ignore_init=True)
    def _close_all_panels():
        _sui.update_accordion("acc", show=False, session=session)


app = App(app_ui, server)
