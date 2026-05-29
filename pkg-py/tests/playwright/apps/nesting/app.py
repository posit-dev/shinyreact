"""Fixture for the interleaved static + reactive nesting e2e test (#88).

Exercises the app.py pattern (page_react + reactive_output) over BOTH delivery
paths for a `Node` tree that interleaves React components with htmltools tags:

1. Static: a `Node("Badge", ...)` embedded in page chrome. `Node.tagify()`
   emits a `.shinyreact-static` mount with an inline JSON `<script>`; the JS
   bundle's `seedInlineSpecs()` pass renders it at load time — no server output.
2. Reactive: a `Node` tree returned from `@reactive_output`, delivered over the
   WebSocket, interleaving an htmltools `tags.div`/`tags.span` with a nested
   registered `Badge` component inside a `Card`.

Expected on screen after load:
  - In #chrome: a badge reading "static-badge".
  - A card titled "Reactive" containing the text "mixed " and a badge
    reading "nested-badge".
"""

from __future__ import annotations

from pathlib import Path

import shinyreact
from htmltools import HTMLDependency, tags
from shiny import App, Inputs, Outputs, Session

_src_dir = Path(__file__).parent
_fixture_dep = HTMLDependency(
    name="nesting-fixture",
    version=str(int((_src_dir / "nesting_fixture.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "nesting_fixture.js", "defer": ""},
)

app_ui = shinyreact.page_react(
    _fixture_dep,
    tags.div(
        shinyreact.Node("Badge", {"text": "static-badge"}),
        id="chrome",
    ),
    shinyreact.ui_output("reactive_card"),
)


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def reactive_card():
        return shinyreact.Node(
            "Card",
            {"title": "Reactive"},
            children=[
                tags.div(
                    tags.span("mixed ", class_="label"),
                    shinyreact.Node("Badge", {"text": "nested-badge"}),
                )
            ],
        )


app = App(app_ui, server)
