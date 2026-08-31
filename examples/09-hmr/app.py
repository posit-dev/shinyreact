from shiny.express import input
from shinyreact import reactive_output, set_react_page

# npm tier: the client imports `@posit/shinyreact` and bundles shinyreact.js
# itself, so the server must not serve it too -- two copies on one page. The
# `#shinyreact-config` tag is still emitted, and the npm client requires it.
set_react_page(shinyreact_js="client")


# `input.count()` is pushed from App.tsx via useShinyInput("count", ...); the
# `doubled` output is read there via useShinyOutputValue("doubled", ...).
@reactive_output
def doubled():
    # Echoes the client-pushed count, doubled — proves the Shiny round-trip
    # keeps working while you hot-edit the client.
    return input.count() * 2
