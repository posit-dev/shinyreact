import plotly.express as px
from shiny import module
from shiny.express import render  # noqa: F401  # marks this file as Shiny Express
from shinyreact import set_react_page
from shinywidgets import render_plotly

set_react_page()


@module.server
def plot_module(input, output, session):
    @render_plotly
    def scatter():
        return px.scatter(x=[1, 2, 3], y=[1, 4, 9])


plot_module("a")
