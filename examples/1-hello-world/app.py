from pathlib import Path

import shinyjsonold as shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session

_src_dir = Path(__file__).parent
_hello_dep = HTMLDependency(
    name="hello-world",
    version=str(int((_src_dir / "hello_world.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "hello_world.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.page_react(
    _hello_dep,
    shinyjson.ui_output("hello"),
)


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
    debounce_ms: int | None = None,
) -> shinyjson.Node:
    props: dict[str, object] = {
        "input_id": input_id,
        "default_value": default_value,
        "placeholder": placeholder,
        "label": label,
    }
    if debounce_ms is not None:
        props["debounce_ms"] = debounce_ms
    return shinyjson.Node(type="TextInput", props=props)


def hr() -> shinyjson.Node:
    return shinyjson.Node(type="Divider")


def input_display(
    input_id: str, *, default_value: str = "", label: str = ""
) -> shinyjson.Node:
    return shinyjson.Node(
        type="InputDisplay",
        props={"input_id": input_id, "default_value": default_value, "label": label},
    )


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
            input_display(
                "txtin", default_value="Hello, world!", label="Client-side value:"
            ),
            output_display("txtout", label="Response from Shiny server:"),
        )

    @shinyjson.render
    def txtout():
        return input.txtin().upper()


app = App(app_ui, server)
