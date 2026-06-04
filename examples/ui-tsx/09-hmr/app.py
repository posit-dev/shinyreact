from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def doubled():
    # Echoes the client-pushed count, doubled — proves the Shiny round-trip
    # keeps working while you hot-edit the client.
    return input.count() * 2
