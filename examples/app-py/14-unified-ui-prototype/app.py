"""End-to-end demo of shinyui's class-per-component hierarchy.

Exercises every reference class in one page:
  - UiInputSlider, UiInputSelect    (simple + structured inputs)
  - UiOutputCode                    (output)
  - UiOutputPlot                    (output with read-only signals)
  - UiCard                          (layout with state)
  - UiAccordion + UiAccordionPanel  (layout-with-state + layout-as-child)

The `app_ui` is a function (not a module-level Tag) so a session is in scope
when components are constructed — this is what enables class-owned bookmark
serializers (and the id->instance registry) to register themselves.

Server code uses `shinyui.lookup_component(session, id)` to fetch the typed
component instance, giving access to:
  - `.value()` / `.full_screen_value()` / `.open_panels()`
    / `.click_value()` / `.brush_value()`
  - `.update(...)` for server-driven changes
"""

from __future__ import annotations

from typing import cast

import shinyui as su
from shiny import App, Inputs, Outputs, Session, reactive, render, ui


def app_ui(request):
    return ui.page_fluid(
        su.card(
            su.input_slider("n", "Sample size", 10, 1000, 100),
            su.input_select(
                "dist",
                "Distribution",
                {"normal": "Normal", "uniform": "Uniform"},
            ),
            su.output_code("summary"),
            su.output_plot("plot", click=True, brush=True),
            su.accordion(
                su.accordion_panel(
                    "Settings",
                    su.input_slider("seed", "Seed", 1, 1000, 42),
                ),
                su.accordion_panel(
                    "Diagnostics",
                    su.output_code("diag"),
                ),
                id="acc",
                open="Settings",
            ),
            id="main_card",
            full_screen=False,
        ),
        title="shinyui Stage A prototype",
    )


def server(input: Inputs, output: Outputs, session: Session):
    # Fetch typed component handles by id from the per-session registry.
    n_slider = cast(su.UiInputSlider, su.lookup_component(session, "n"))
    seed_slider = cast(su.UiInputSlider, su.lookup_component(session, "seed"))
    dist_select = cast(su.UiInputSelect, su.lookup_component(session, "dist"))
    main_card = cast(su.UiCard, su.lookup_component(session, "main_card"))
    acc = cast(su.UiAccordion, su.lookup_component(session, "acc"))
    plot_handle = cast(su.UiOutputPlot, su.lookup_component(session, "plot"))

    @render.code
    def summary():
        # Reads via class-level accessor — no input.n() / input.dist() needed.
        return (
            f"n     = {n_slider.value()}\n"
            f"dist  = {dist_select.value()}\n"
            f"seed  = {seed_slider.value()}\n"
            f"open  = {acc.open_panels()}\n"
            f"fs    = {main_card.full_screen_value()}\n"
        )

    @render.code
    def diag():
        click = plot_handle.click_value()
        brush = plot_handle.brush_value()
        return f"click = {click}\nbrush = {brush}"

    @render.plot
    def plot():
        # Minimal placeholder — shows click/brush target area.
        import matplotlib.pyplot as plt  # type: ignore[import-not-found]

        fig, ax = plt.subplots()
        ax.text(
            0.5,
            0.5,
            "Click or brush to populate diag panel.",
            ha="center",
            va="center",
        )
        ax.set_axis_off()
        return fig

    # Server-driven updates on layouts-with-state:
    @reactive.effect
    def _auto_expand_at_high_n():
        if n_slider.value() > 800:
            main_card.update(full_screen=True)
            acc.update(open=("Settings", "Diagnostics"))


app = App(app_ui, server)
