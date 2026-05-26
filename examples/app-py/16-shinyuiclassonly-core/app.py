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
    ``acc.open_panels()`` / ``main_card.full_screen_value()`` /
    ``plot.click_value()``.
  - Updates use ``shiny.ui.update_accordion(...)`` directly instead of
    ``acc.update(...)``.
  - The plot renderer (``shinyuiclassonly.render_plot``) still carries
    the interaction flags and auto-places its ``output_plot``; it just
    no longer carries ``.click_value`` / ``.brush_value`` accessors.

The architectural delta between this file and example 14 is the cost of
the session-bound machinery that ``shinyui`` adds on top of the class
hierarchy.
"""

from __future__ import annotations

import shinyuiclassonly as su
from shiny import App, Inputs, Outputs, Session, reactive, render
from shiny import ui as _sui

# --- UI ---------------------------------------------------------------------

btn1=
btn2=        su.input_action_button("close_all", "Close all panels")

# Current Express: Use display hooks to route render
# Used only within "express"
with ui.hold():
    with su.card() as main_card:
        with _sui.layout_column_wrap(width=1 / 2):
            ui.markdown("Extra content")

            "Extra content"
            42

            su.input_action_button("open_all", "Open all panels")
            btn2

# Proposal: Stack only; Hook exists within the `__init__`
# Used within "core" apps; Also "express" mode
# All components must be "wrapped"!!
# No ui.hold(); Only simple ctx stack management
# Prefab UI style

from shiny import input, output, session # similar to express mode

with global_session():
    @reactive.calc
    def first_content():
        return str(42)

# BE AWARE!!:
# * display hooks are used within notebooks; Validate the behavior of the hooks
# * Maybe we could escape it and have the print method not "print to screen" if the stack level is >= 1?

# All inputs at top level to store into variable

# Top level will not "print". Only sets variable
open_btn = su.input_action_button("open_all", "Open all panels")

# Team:
# * Stack is good;
# * Capture during `__init__`; Allow for `.display()` to "init" within a sep stack
# * Allows for both assignment and just "printing" the component;
# * Will require reactive objects to be session lazy and handle multiple sessions;
# * Leverages UI class mechanisms to manage the stack and capture;
#   * Uses tagify to convert to Tags

# Impl Now:
# * PR to `dev` - put in md docs / plans
#   * Commit superpower plan/design docs; Delete them later
#   * Step in path towards: "How to display a component" - Instead of immediate "to DOM", it decouples intent from implementation. Allows an entry point to print using a new mechanism (ex: react.js).
#     * Future - could be json that is rendered client-side via react.js / vue / svelte / etc. instead of rendered server-side via tagify

# * Use a `dev` v2 branch!
# * Ui Classes are a good idea; It is independent of the stack mechanism and can be used in both express and core;
#   * Get basic classes working first
#   * Open Question: syntax for value / update methods
# * Stack implementation - Change "Express" mental model
#   * Require that Express mode items are "wrapped" so they can be captured
#   * Breaking changes - Require shiny v2
#     * Requires doc of all pros/cons and migration path;

# Impl later:
# * Core mode w/ stack
#   * Requires that all components are "wrapped" so they can be captured
# * Stack implementation is a big lift for docs and future development
# * How far away are we to get "express" style within core mode? - Only run the code once
#   * Or the answer is "core" is "have server function", and "express" is "don't have server function and use display hooks to capture values"

# `main_card` is not "printed", it is only set
with su.card() as main_card:
    with _sui.layout_column_wrap(width=1 / 2):
        with ui.hold():
            mymark = ui.markdown("Extra content")
        mymark

        "Extra content" # No longer possible!
        42 # No longer possible!

        ui.markdown(42) # div(span(42)) -> div(), span(42); Safety hatch - use tagify to escape the capture stack
        open_btn = su.input_action_button("open_all", "Open all panels")
        open_btn
        su.input_action_button("close_all", "Close all panels")

        # Displays and sets variable
        open_btn = su.input_action_button("open_all", "Open all panels")

        su.output_code("summary")

        @module
        def mymod(input, output, session):
            ui.markdown("More extra content")
            ui.markdown(first_content())
            su.input_action_button("mod_btn", "Module button")

        # Woudl require that it is aware of all values for every session
        # as there is only "one" extra_content() function that is shared across sessions. Would need to be able to route values based on session context.
        @reactive.calc
        def extra_content():
            input.myvalue()
            return "Extra content\n" + first_content()

        # express only
        @render.code # currently, super greedy and wants a session NOW
        # Proposal: delay session requirement until later
        def extra():
            return extra_content()

@render.code
def summary():
    return extra_content()

app = App(main_card)








    a = su.accordion(
        su.accordion_panel(
            "Settings",
            su.input_slider("n", "Sample size", 10, 1000, 100),
            su.input_select(
                "dist",
                "Distribution",
                {"normal": "Normal", "uniform": "Uniform"},
            ),
            su.input_slider("seed", "Seed", 1, 1000, 42),
        )
    )

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
        return f"click = {input.plot_click()}\nbrush = {input.plot_brush()}\n"

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
