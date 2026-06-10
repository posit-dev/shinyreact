import plotly.express as px
from shiny.express import input, render  # noqa: F401  # marks Express
from shinyreact import set_react_page
from shinywidgets import output_widget, render_plotly

set_react_page()


# Dynamic UI: the widget placeholder only exists in the DOM once the React
# checkbox sets `input.show()` to True.
@render.ui
def holder():
    if not input.show():
        return None
    return output_widget("scatter")


# `scatter` is top-level, so set_react_page() harvests its ipywidget
# dependency into <head> at startup. The dynamic part under test is that the
# chart actually mounts inside `holder` only once the checkbox reveals the
# output_widget — Shiny binds it and renders the figure on demand.
@render_plotly
def scatter():
    return px.scatter(x=[1, 2, 3], y=[1, 4, 9])
