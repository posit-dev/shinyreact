# End-to-end demo of shinyui's class-per-component hierarchy in `with` form.
#
# This is the Express-with-blocks variant of `14-unified-ui-prototype/`. The
# two apps produce the same UI tree. Compare:
#
#   - `14-unified-ui-prototype/app.py` — Shiny Core, positional composition:
#     `card(accordion(accordion_panel("Settings", n_slider, ...), ...), ...)`
#   - This file — Shiny Express, context-manager composition:
#     `with card(): with accordion(): with accordion_panel("Settings"): ...`
#
# Both rely on `@expressify` (Shiny Express's default for `app.py`) so bare
# expression statements get rewritten to `sys.displayhook(...)` calls. The
# shinyui parent-tag context stack (issue #70) routes those values to the
# innermost active `with` parent.
#
# Inputs are constructed AT THEIR DISPLAY POINT via the walrus operator
# (`(n_slider := su.input_slider(...))`), so the same statement both places
# the input in the active parent (via `sys.displayhook` routing) and binds
# a module-scope name that the renderers below can read from. The renderer
# `def` statements are placed INSIDE the `with` block that should display
# them — Express's expressify hook fires `sys.displayhook(fn)` after every
# top-level function def whose result is `Tagifiable`. Renderers are
# Tagifiable, so the displayhook fires and our parent stack routes the
# renderer's UI to the active `with` parent. No `output_code(...)`
# placeholder is needed — the renderer IS the placement. The plot renderer
# (`shinyui.render_plot`) carries the interaction config and accessors
# (`click_value`, `brush_value`, etc.).
#
# A module-level docstring would render as raw text on the page because
# Express's `@expressify` wraps every bare-expression statement (including
# the docstring) in `sys.displayhook(...)`. So this module uses a comment
# block instead. A small `ui.markdown(...)` header at the top of the page
# below introduces the demo to the user.

from __future__ import annotations

import shinyui as su
from shiny import reactive, render
from shiny import ui as _sui
from shiny.express import ui

# --- Page ------------------------------------------------------------------
ui.page_opts(title="shinyui Stage A — with-block form")

ui.markdown(
    """
    ### shinyui Stage A — Express with-blocks

    This is the Express variant of `14-unified-ui-prototype/` — same components,
    same tree, expressed as `with card(): with accordion(): ...`. Both files
    render identical UI; the difference is the composition idiom. See
    [issue #70](https://github.com/posit-dev/shinyreact/issues/70).
    """
)

# Build the UI tree with `with` blocks. Express's @expressify rewrite turns
# each bare expression below into `sys.displayhook(value)`; shinyui's parent
# stack routes them to the active `with` parent. The walrus operator
# (`(name := expr)`) lets us BOTH place the component in the active parent
# AND bind a module-scope name in the same statement, so the renderer
# defs below can reference inputs by their bound names (e.g.
# `n_slider.value()`).
with su.card(id="main_card", full_screen=False) as main_card:
    _sui.layout_column_wrap(
        (open_all_btn := su.input_action_button("open_all", "Open all panels")),
        (close_all_btn := su.input_action_button("close_all", "Close all panels")),
        width=1 / 2,
    )
    with su.accordion(id="acc", open="Settings") as acc:
        with su.accordion_panel("Settings"):
            (n_slider := su.input_slider("n", "Sample size", 10, 1000, 100))
            (
                dist_select := su.input_select(
                    "dist",
                    "Distribution",
                    {"normal": "Normal", "uniform": "Uniform"},
                )
            )
            (seed_slider := su.input_slider("seed", "Seed", 1, 1000, 42))
        with su.accordion_panel("Diagnostics"):

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
