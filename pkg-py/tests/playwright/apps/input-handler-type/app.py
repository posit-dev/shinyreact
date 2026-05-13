from shiny.express import input, render  # noqa: F401  # marks this file as Shiny Express
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def when_info():
    v = input.when()
    if v is None:
        return "pending"
    return type(v).__name__
