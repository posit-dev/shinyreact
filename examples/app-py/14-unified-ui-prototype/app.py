"""End-to-end demo of shinyui's class-per-component hierarchy in **Shiny Core**.

This is the Core (positional composition) variant. Its sibling
``15-shinyui-with-blocks/app.py`` builds the same UI tree in Shiny Express
using ``with``-blocks. Together they demonstrate the unified API from
issue #70: a single set of ``shinyui`` classes that work in both idioms.

  - **This file** (Core): ``app_ui = ui.page_fluid(card(accordion(panel(...))))``
    plus a ``server(input, output, session)`` function.
  - **Example 15** (Express): ``with card(): with accordion(): with panel(): ...``
    plus ``@render.*`` inside the active ``with`` block.

The same component classes (``card``, ``accordion``, ``accordion_panel``,
``input_slider``, etc.) compose identically in both modes. The server-side
accessors (``slider.value()``, ``acc.update(...)``, ``card.value_full_screen()``)
work the same in both — they resolve the active root session at call time, so
they are safe to define at module load in Core and access from inside the
``server`` function (see ``UiComponent._require_session`` for how the
unification works).

This file uses the **walrus operator** to construct and bind every component
inline inside the single ``app_ui = page_fluid(card(...))`` expression. The
walrus assignment (`(n_slider := su.input_slider(...))`) places the input in
its positional slot AND binds a module-scope name that the ``server`` function
reads via ``n_slider.value()``. Same trick as example 15 (where the walrus
runs inside ``with`` blocks); here it runs inside positional ``card(...)`` /
``accordion(...)`` calls.

The plot uses :class:`shinyui.render_plot`, which owns the derived-input
accessors (``value_click``, ``value_brush``, etc.). In Core, ``output_plot``
in ``app_ui`` provides placement; the matching ``@su.render_plot(...)`` in
``server`` provides the renderer plus the derived-input accessors.
"""

from __future__ import annotations

import shinyui as su
from shiny import App, Inputs, Outputs, Session, reactive, render
from shiny import ui as _sui

# --- UI ---------------------------------------------------------------------
# Build the whole UI tree as a single expression. Walrus operators
# (`(name := expr)`) inside the tree bind module-scope names so the
# `server(input, output, session)` function below can read inputs via
# `n_slider.value()`, push updates via `acc.update(...)`, etc.
app_ui = _sui.page_fluid(
    (
        main_card := su.card(
            _sui.layout_column_wrap(
                (open_all_btn := su.input_action_button("open_all", "Open all panels")),
                (close_all_btn := su.input_action_button("close_all", "Close all panels")),
                width=1 / 2,
            ),
            (
                acc := su.accordion(
                    su.accordion_panel(
                        "Settings",
                        (n_slider := su.input_slider("n", "Sample size", 10, 1000, 100)),
                        (
                            dist_select := su.input_select(
                                "dist",
                                "Distribution",
                                {"normal": "Normal", "uniform": "Uniform"},
                            )
                        ),
                        (seed_slider := su.input_slider("seed", "Seed", 1, 1000, 42)),
                    ),
                    su.accordion_panel(
                        "Diagnostics",
                        su.output_code("summary"),
                        su.output_code("diag"),
                    ),
                    id="acc",
                    open="Settings",
                )
            ),
            su.output_plot("plot", click=True, brush=True),
            id="main_card",
            full_screen=False,
        )
    ),
    title="shinyui Stage A — Core (positional) form",
)


# --- Server -----------------------------------------------------------------
def server(input: Inputs, output: Outputs, session: Session) -> None:
    @render.code
    def summary() -> str:
        return (
            f"n     = {n_slider.value()}\n"
            f"dist  = {dist_select.value()}\n"
            f"seed  = {seed_slider.value()}\n"
            f"open  = {acc.open_panels()}\n"
            f"fs    = {main_card.value_full_screen()}\n"
        )

    @render.code
    def diag() -> str:
        return (
            f"click = {plot.value_click()}\n"
            f"brush = {plot.value_brush()}\n"
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

    @reactive.effect
    @reactive.event(open_all_btn.value, ignore_init=True)
    def _open_all_panels():
        acc.update(open=("Settings", "Diagnostics"))

    @reactive.effect
    @reactive.event(close_all_btn.value, ignore_init=True)
    def _close_all_panels():
        acc.update(open=False)


app = App(app_ui, server)
