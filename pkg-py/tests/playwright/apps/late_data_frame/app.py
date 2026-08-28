import pandas as pd
from shiny import reactive
from shiny.express import render  # noqa: F401  # marks the file as Express
from shinyreact import set_react_page

set_react_page()


# `grid` is registered from inside an effect, so it does not exist when the
# page HTML is generated: set_react_page()'s harvest cannot inline the
# `shiny-data-frame-output` dependency (`data-frame.js`) into <head>. And
# unlike apps/dynamic_plotly there is no `@render.ui` holder, so Shiny's own
# dynamic-UI dependency path never runs either. The only route left for the
# binding to reach the client is shinyreact's post-flush dep push (#220) —
# without it, <shiny-data-frame> stays an unbound, empty custom element.
@reactive.effect
def _register_grid():
    @render.data_frame
    def grid():
        return pd.DataFrame({"letter": ["alpha", "beta"], "number": [1, 2]})
