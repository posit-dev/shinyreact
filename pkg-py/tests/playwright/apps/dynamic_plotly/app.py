import plotly.express as px
from shiny import reactive
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


# Register `scatter` from inside an effect so registration happens in the real
# session, *after* page HTML is generated. A top-level renderer (even under
# `ui.hold()`) lands in the stub session's outputs and the Layer-A harvest
# would pre-inject its ipywidget dependency into the initial <head> — making
# any "dynamic delivery" assertion vacuous. Registered here, the dependency
# can only reach the client through Shiny's dynamic-UI path when `holder`
# renders the `output_widget`.
@reactive.effect
def _register_scatter():
    @render_plotly
    def scatter():
        return px.scatter(x=[1, 2, 3], y=[1, 4, 9])
