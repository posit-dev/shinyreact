from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()


# Changes on every toggle, so the server pushes a new value while the reader
# is unmounted too: a leaked binding would receive it and log "not found".
@reactive_output
def toggles():
    return f"toggles: {input.toggles()}"
