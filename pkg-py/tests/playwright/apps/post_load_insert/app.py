"""Fixture proving static `.shinyreact-static` mounts inserted AFTER page load
are not seeded today (#120).

Two `Node`-bearing regions, both using the app.py pattern (page_react):

1. Control — a static `Node("Badge", ...)` in page chrome, present at load.
   `Node.tagify()` emits a `.shinyreact-static` mount; the JS bundle's
   one-shot `seedInlineSpecs()` (DOMContentLoaded) renders it. This WORKS.

2. Bug — a `@render.ui` output that returns a `Node` only after an action
   button is clicked. The Node tagifies to the same `.shinyreact-static`
   shape, but it is inserted into the DOM over the WebSocket *after* load,
   so the one-shot seeding pass never sees it. The mount lands in the DOM
   but renders nothing.

Expected on screen after load:
  - In #chrome: a badge reading "static-badge".
  - #panel empty until "Show panel" is clicked; after the click a badge
    reading "dynamic-badge" SHOULD appear (it does not, today — that is the
    bug under test).
"""

from __future__ import annotations

from pathlib import Path

import shinyreact
from htmltools import HTMLDependency, tags
from shiny import App, Inputs, Outputs, Session, render, ui

_src_dir = Path(__file__).parent
_fixture_dep = HTMLDependency(
    name="post-load-insert-fixture",
    version=str(int((_src_dir / "post_load_insert_fixture.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "post_load_insert_fixture.js", "defer": ""},
)

app_ui = shinyreact.page_react(
    _fixture_dep,
    tags.p(
        "Click 'Show panel'. The badge reading 'dynamic-badge' should appear "
        "inside #panel. It does not today (#120)."
    ),
    tags.div(
        shinyreact.Node("Badge", {"text": "static-badge"}),
        id="chrome",
    ),
    ui.input_action_button("show", "Show panel"),
    tags.div(ui.output_ui("panel"), id="panel"),
)


def server(input: Inputs, output: Outputs, session: Session):
    @render.ui
    def panel():
        if input.show() == 0:
            return None
        return shinyreact.Node("Badge", {"text": "dynamic-badge"})


app = App(app_ui, server)
