import plotly.express as px
from shiny.express import input, render, ui  # noqa: F401  # marks Express
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


# `with ui.hold()` suppresses the auto-display of `scatter`'s own placeholder —
# the chart appears only via the `output_widget("scatter")` that `holder`
# reveals on demand, never as a stray top-level output.
with ui.hold():

    @render_plotly
    def scatter():
        return px.scatter(x=[1, 2, 3], y=[1, 4, 9])
