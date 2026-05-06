import pandas as pd
from shiny.express import input, render
from shinyreact import reactive_output, set_page

set_page()


@reactive_output
def greeting():
    n = input.row_count()
    return f"Showing {n} rows"


@render.data_frame
def my_table():
    n = input.row_count()
    df = pd.DataFrame(
        {
            "Name": [f"Item {i}" for i in range(1, n + 1)],
            "Value": [i * 10 for i in range(1, n + 1)],
            "Category": [("A" if i % 2 == 0 else "B") for i in range(1, n + 1)],
        }
    )
    return df
