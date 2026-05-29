"""14-nesting: htmltools and React components interleaved in one tree.

Demonstrates "layer all the way down": htmltools `tags.*` and shinyreact
`Node`s nest inside each other at arbitrary depth, in both the static
page-chrome path and a reactive @reactive_output.
"""

from pathlib import Path

import shinyreact
from htmltools import HTMLDependency, tags
from shiny import App, Inputs, Outputs, Session

_src_dir = Path(__file__).parent
_dep = HTMLDependency(
    name="nesting-example",
    version=str(int((_src_dir / "nesting.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "nesting.js", "defer": ""},
)

app_ui = shinyreact.page_react(
    _dep,
    tags.div(
        tags.h1("Nesting demo"),
        # A React component embedded directly in htmltools chrome.
        shinyreact.Node("Badge", {"text": "I am a React component in chrome"}),
        tags.p("…and this is plain htmltools text."),
    ),
    shinyreact.ui_output("card"),
)


def server(input: Inputs, output: Outputs, session: Session) -> None:
    @shinyreact.reactive_output
    def card():
        return shinyreact.Node(
            "Card",
            {"title": "Mixed content"},
            children=[
                tags.div(
                    tags.strong("htmltools "),
                    "wrapping ",
                    shinyreact.Node("Badge", {"text": "a nested React badge"}),
                ),
            ],
        )


app = App(app_ui, server)
