from shiny import reactive
from shiny.express import app_opts, input, render, session  # noqa: F401
from shinyreact import reactive_output, set_react_page

# `bookmark_store="url"` makes Shiny parse `?_inputs_&...` into a RestoreContext
# and (in server-mode) write `?_state_id_=...` after a `session.bookmark()`.
app_opts(bookmark_store="url")
set_react_page()


@reactive_output
def echo() -> str:
    chk = "yes" if input.chk() else "no"
    return f"text={input.txt()!r} num={input.num()} checked={chk}"


# Without this, Shiny shows the URL in a Bootstrap modal, which this
# Bootstrap-free page cannot open (#326).
session.bookmark.on_bookmarked(session.bookmark.update_query_string)


@reactive.effect
@reactive.event(input.bookmark_clicks, ignore_init=True)
async def _on_bookmark_click() -> None:
    await session.bookmark()
