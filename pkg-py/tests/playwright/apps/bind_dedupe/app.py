import shinyreact
from shiny.express import input, render, ui  # noqa: F401  # marks Express
from shinyreact import set_react_page

set_react_page()


# Three `@render.ui` holders, hosted side by side in one parent by the React
# client: the shape #298 found the duplicate-binding race in (a sidebar of
# `renderUI()` widgets). Each one is a real, bindable Shiny output from the
# moment it mounts, so every `ShinyOutput` mounting under that parent triggers
# a `Shiny.bindAll()` pass over all of them.
@render.ui
def widgets_a():
    return ui.input_slider("bins_a", "A", min=1, max=50, value=9)


@render.ui
def widgets_b():
    return ui.input_slider("bins_b", "B", min=1, max=50, value=19)


# Mounted by the client one commit *after* the two above (see www/app.js).
@render.ui
def widgets_late():
    return ui.input_selectize("letter", "Letter", choices=["a", "b", "c"])


# Hosted by the client in a `div` *inside* the parent of the three above, so
# its scope and theirs are two different elements that nonetheless scan the
# same subtree: `bindAll` is descendants-only, so the outer pass walks these
# too. The shape #301 found.
@render.ui
def widgets_nested():
    return ui.input_slider("bins_nested", "Nested", min=1, max=50, value=29)


# Same late commit as `widgets_late`, but under the nested parent: this is the
# combination that needs the queued pass to wait for the *overlapping* outer
# pass as well as for its own scope's.
@render.ui
def widgets_nested_late():
    return ui.input_selectize("nested_letter", "Nested letter", choices=["x", "y"])


@shinyreact.reactive_output
def echo():
    return {
        "a": input.bins_a(),
        "b": input.bins_b(),
        "letter": input.letter(),
        "nested": input.bins_nested(),
        "nested_letter": input.nested_letter(),
    }
