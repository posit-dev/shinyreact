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
# Component helpers — thin wrappers around shinyjson.Element that mirror the
# registered JS components in hello_world.js.
# ---------------------------------------------------------------------------
def Card(title: str, children: list[str]) -> shinyjson.Element:
    return shinyjson.Element(type="Card", props={"title": title}, children=children)


def TextInput(
    input_id: str,
    default_value: str = "",
    *,
    placeholder: str = "",
    label: str = "",
) -> shinyjson.Element:
    return shinyjson.Element(
        type="TextInput",
        props={
            "input_id": input_id,
            "default_value": default_value,
            "placeholder": placeholder,
            "label": label,
        },
    )


def Divider() -> shinyjson.Element:
    return shinyjson.Element(type="Divider", props={})


def OutputDisplay(output_id: str, *, label: str = "") -> shinyjson.Element:
    return shinyjson.Element(
        type="OutputDisplay", props={"output_id": output_id, "label": label}
    )


# ---------------------------------------------------------------------------


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def hello():
        return shinyjson.Spec(
            root="card",
            elements={
                "card": Card("Hello Shiny React!", children=["input1", "hr", "out1"]),
                "input1": TextInput(
                    "txtin",
                    "Hello, world!",
                    placeholder="Enter your message here...",
                    label="Type something to send to Shiny server:",
                ),
                "hr": Divider(),
                "out1": OutputDisplay("txtout", label="Response from Shiny server:"),
            },
        )

    @shinyjson.render
    def txtout():
        return input.txtin().upper()


app = App(app_ui, server)
