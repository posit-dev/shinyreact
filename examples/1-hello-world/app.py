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
            root="hw",
            elements={
                "hw": shinyjson.Element(type="HelloWorldComponent", props={}),
            },
        )

    @shinyjson.render
    def txtout():
        return input.txtin().upper()


app = App(app_ui, server)
