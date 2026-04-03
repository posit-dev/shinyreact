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


# ---------------------------------------------------------------------------
# Component helpers — thin wrappers around shinyjson.Node that mirror the
# registered JS components in hello_world.js.
# ---------------------------------------------------------------------------
def card(title: str, *children: shinyjson.Node) -> shinyjson.Node:
    return shinyjson.Node(type="Card", props={"title": title}, children=list(children))


def text_input(
    input_id: str,
    default_value: str = "",
    *,
    placeholder: str = "",
    label: str = "",
) -> shinyjson.Node:
    return shinyjson.Node(
        type="TextInput",
        props={
            "input_id": input_id,
            "default_value": default_value,
            "placeholder": placeholder,
            "label": label,
        },
    )


def hr() -> shinyjson.Node:
    return shinyjson.Node(type="Divider")


def output_display(output_id: str, *, label: str = "") -> shinyjson.Node:
    return shinyjson.Node(
        type="OutputDisplay", props={"output_id": output_id, "label": label}
    )


# ---------------------------------------------------------------------------


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def hello():
        return card(
            "Hello Shiny React!",
            text_input(
                "txtin",
                "Hello, world!",
                placeholder="Enter your message here...",
                label="Type something to send to Shiny server:",
            ),
            hr(),
            output_display("txtout", label="Response from Shiny server:"),
        )

    @shinyjson.render
    def txtout():
        return input.txtin().upper()


app = App(app_ui, server)
