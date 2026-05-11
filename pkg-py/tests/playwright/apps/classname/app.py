from shiny.express import render  # noqa: F401  # marks this file as Shiny Express
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def out():
    return "hi"
