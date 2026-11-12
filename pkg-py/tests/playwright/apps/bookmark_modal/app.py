from shiny import reactive
from shiny.express import app_opts, input, session
from shinyreact import set_react_page

app_opts(bookmark_store="url")
set_react_page()


# No `on_bookmarked()` callback, so Shiny falls back to its Bootstrap modal.
@reactive.effect
@reactive.event(input.bookmark_clicks, ignore_init=True)
async def _() -> None:
    await session.bookmark()
