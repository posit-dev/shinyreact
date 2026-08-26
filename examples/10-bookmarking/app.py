import shinyreact
from shiny import Inputs, Outputs, Session, reactive
from shinyreact import ReactApp


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def greeting() -> str:
        chk_label = "yes" if input.chk() else "no"
        return f"text={input.txt()!r} num={input.num()} checked={chk_label}"

    @reactive.effect
    @reactive.event(input.bookmark_clicks, ignore_init=True)
    async def _on_bookmark_click() -> None:
        await session.bookmark()


# ReactApp discovers www/ui.js + www/ui.css and re-renders the page per
# request, so the bookmark restore payload lands in #shinyreact-config.
app = ReactApp(server, bookmark_store="url")
