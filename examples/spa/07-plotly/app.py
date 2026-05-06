import numpy as np
import plotly.express as px
from shiny.express import input
from shinyreact import reactive_output, set_page
from shinywidgets import render_plotly

set_page()


@reactive_output
def greeting():
    n = input.num_points()
    return f"Showing {n} random points"


@render_plotly
def scatter():
    n = input.num_points()
    rng = np.random.default_rng(42)
    x = rng.normal(size=n)
    y = rng.normal(size=n)
    fig = px.scatter(x=x, y=y, title=f"Random Scatter ({n} points)")
    fig.update_layout(margin=dict(l=40, r=20, t=40, b=40))
    return fig
