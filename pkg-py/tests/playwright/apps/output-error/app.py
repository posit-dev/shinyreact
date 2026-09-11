from shiny import req
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def answer():
    n = input.n()
    if n == -2:
        # An error whose message is empty. Python never produces this for
        # `req()` (py-shiny sends a `null` value instead), but R's `req()` does
        # put exactly this on the wire, so it is how we exercise the client's
        # silent-error branch from a Python fixture.
        raise ValueError("")
    # n < 0 is a *silent* error: no message reaches the client.
    req(n is not None and n >= 0)
    if n == 0:
        raise ValueError("invalid number of 'breaks'")
    return f"ok: {n}"
