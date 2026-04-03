from pathlib import Path

import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session

_hello_dep = HTMLDependency(
    name="hello-world",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "hello_world.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("hello", extra_deps=[_hello_dep])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def hello():
        return shinyjson.Spec(
            root="card",
            elements={
                "card": shinyjson.Element(
                    type="Card",
                    props={"title": "Hello Shiny React!"},
                    children=["input1", "hr", "display1"],
                ),
                "input1": shinyjson.Element(
                    type="TextInput",
                    props={
                        "input_id": "txtin",
                        "default_value": "Hello, world!",
                        "placeholder": "Enter your message here...",
                        "label": "Type something to send to Shiny server:",
                    },
                ),
                "hr": shinyjson.Element(type="Divider", props={}),
                "display1": shinyjson.Element(
                    type="OutputDisplay",
                    props={
                        "output_id": "txtout",
                        "label": "Response from Shiny server:",
                    },
                ),
            },
        )

    @shinyjson.render
    def txtout():
        return input.txtin().upper()


app = App(app_ui, server)
