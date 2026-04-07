import random
from pathlib import Path

import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive

_src_dir = Path(__file__).parent
_messages_dep = HTMLDependency(
    name="messages-example",
    version=str(int((_src_dir / "messages.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "messages.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("main", extra_deps=[_messages_dep])


# ---------------------------------------------------------------------------
# Component helpers — thin wrappers around shinyjson.Node that mirror the
# registered JS components in messages.js.
# ---------------------------------------------------------------------------
def app_layout(title: str, *children: shinyjson.Node) -> shinyjson.Node:
    return shinyjson.Node(
        type="AppLayout", props={"title": title}, children=list(children)
    )


def toast_card(title: str) -> shinyjson.Node:
    return shinyjson.Node(type="ToastCard", props={"title": title})


# ---------------------------------------------------------------------------


def server(input: Inputs, output: Outputs, session: Session):
    # Simulate log events
    log_messages = [
        {"text": "User logged in", "category": "info"},
        {"text": "File saved successfully", "category": "success"},
        {"text": "Low disk space warning", "category": "warning"},
        {"text": "Backup completed", "category": "success"},
        {"text": "Processing data...", "category": "info"},
        {"text": "Cache cleared", "category": "info"},
    ]

    @shinyjson.render
    def main():
        return app_layout(
            "Event Message Demo",
            toast_card("Toast messages from server"),
        )

    @reactive.effect
    async def _():
        # Timer that triggers every 2 seconds
        reactive.invalidate_later(2)
        log_event = random.choice(log_messages)
        await shinyjson.post_message(session, "logEvent", log_event)


app = App(app_ui, server)
