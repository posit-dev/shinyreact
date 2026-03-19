from pathlib import Path
import random

import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive

_messages_dep = HTMLDependency(
    name="messages-example",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "messages.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("main", extra_deps=[_messages_dep])


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
        return shinyjson.Spec(
            root="app",
            elements={
                "app": shinyjson.Element(type="App", props={}),
            },
        )

    @reactive.effect
    async def _():
        # Timer that triggers every 2 seconds
        reactive.invalidate_later(2)
        log_event = random.choice(log_messages)
        await shinyjson.post_message(session, "logEvent", log_event)


app = App(app_ui, server)
