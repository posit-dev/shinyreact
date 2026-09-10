import shinyreact
from shiny import reactive
from shiny.express import input, render, session, ui  # noqa: F401  # marks Express
from shinyreact import set_react_page

set_react_page()


# A *real* Shiny input widget hosted inside the React client: the server owns
# the markup and its dependencies (ion-rangeslider, selectize), Shiny's
# html-output binding calls `initializeInputs()` + `bindAll()` on arrival, so
# `input.bins()` / `input.letter()` behave exactly as in a classic app.
@render.ui
def widgets():
    return ui.TagList(
        ui.input_slider("bins", "Bins", min=1, max=50, value=9),
        ui.input_selectize("letter", "Letter", choices=["a", "b", "c"]),
    )


@shinyreact.reactive_output
def echo():
    return {"bins": input.bins(), "letter": input.letter()}


# Server-driven updates keep working on the hosted widgets.
@reactive.effect
@reactive.event(input.bump, ignore_init=True)
def _bump():
    ui.update_slider("bins", value=42)
    ui.update_selectize("letter", selected="c")
