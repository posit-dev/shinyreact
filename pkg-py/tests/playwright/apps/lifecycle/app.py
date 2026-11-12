import time

from shiny import reactive
from shiny.express import input, session
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
@reactive.event(input.slow, ignore_init=True)
def slow():
    # Long enough for the client to see `shiny:busy` before `shiny:idle`.
    time.sleep(1)
    return input.slow()


@reactive.effect
@reactive.event(input.close, ignore_init=True)
async def _():
    await session.close()
