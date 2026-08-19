from pathlib import Path

import shinyreact
from shiny import App, Inputs, Outputs, Session, reactive


def app_ui(request):
    # A function-of-request UI makes Shiny re-render the page per request, so
    # page_react_html() sees the active RestoreContext and emits the restore
    # <script> tag when a bookmark query string is present.
    return shinyreact.page_react_html("www/index.html")


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def greeting() -> str:
        chk_label = "yes" if input.chk() else "no"
        return f"text={input.txt()!r} num={input.num()} checked={chk_label}"

    @reactive.effect
    @reactive.event(input.bookmark_clicks, ignore_init=True)
    async def _on_bookmark_click() -> None:
        await session.bookmark()


# Core apps must mount www/ themselves — App() has no equivalent of Shiny
# Express's automatic www/ static mount.
app = App(
    app_ui,
    server,
    static_assets={"/": Path(__file__).parent / "www"},
    bookmark_store="url",
)
