import pandas as pd
from shiny.express import render
from shinyreact import set_react_page

set_react_page()


@render.data_frame
def my_table():
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})
