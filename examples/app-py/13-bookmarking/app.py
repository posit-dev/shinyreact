from pathlib import Path

import shinyreact
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive

_src_dir = Path(__file__).parent
_dep = HTMLDependency(
    name="bookmarking-example",
    version=str(int((_src_dir / "bookmarking.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "bookmarking.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)


def app_ui(request):
    # page_react picks up the active RestoreContext (if any) and emits the
    # restore <script> tag automatically via _dep_page().
    return shinyreact.page_react(_dep, title="shinyreact bookmarking")


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def greeting() -> str:
        chk_label = "yes" if input.chk() else "no"
        return f"text={input.txt()!r} num={input.num()} checked={chk_label}"

    @reactive.effect
    @reactive.event(input.bookmark_clicks, ignore_init=True)
    async def _on_bookmark_click() -> None:
        await session.bookmark()


app = App(app_ui, server, bookmark_store="url")
