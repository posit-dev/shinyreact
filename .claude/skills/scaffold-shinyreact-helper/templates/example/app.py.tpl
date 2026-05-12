"""{{pkg}} prototype example app — scaffolded by scaffold-shinyreact-helper."""

import {{pkg}}
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[{{pkg}}.dep()])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        clicks = input.b1() or 0
        return shinyreact.Node(
            type="div",
            props={
                "style": {
                    "padding": "16px",
                    "fontFamily": "sans-serif",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "16px",
                }
            },
            children=[
                shinyreact.Node(type="h1", props={"children": "{{pkg}} prototype"}),
                {{pkg}}.{{stub}}("Click me", input_id="b1"),
                shinyreact.Node(
                    type="div",
                    props={"children": f"Stub button clicks: {clicks}"},
                ),
            ],
        )


app = App(app_ui, server)
