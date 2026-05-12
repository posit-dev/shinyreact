"""shinymui prototype example app.

Mounts each MUI component as it is added in subsequent tasks. Starts as
plumbing-only: renders a static heading to confirm the bundle loads.
"""

import shinymui
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[shinymui.dep()])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        return shinyreact.Node(
            type="div",
            props={"style": {"padding": "16px", "fontFamily": "sans-serif"}},
            children=[
                shinyreact.Node(
                    type="h1",
                    props={},
                    children=[shinyreact.Node(type="span", props={"children": "shinymui prototype"})],
                ),
                shinyreact.Node(
                    type="p",
                    props={"children": "Plumbing test. Components added in following tasks."},
                ),
            ],
        )


app = App(app_ui, server)
