from shiny import req
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def answer():
    n = input.n()
    # n < 0 is a *silent* error: no message reaches the client.
    req(n is not None and n >= 0)
    if n == 0:
        raise ValueError("invalid number of 'breaks'")
    return f"ok: {n}"
