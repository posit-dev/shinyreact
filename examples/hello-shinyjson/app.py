from pathlib import Path

import shinyjsonold as shinyjson
from htmltools import HTMLDependency
from shiny.express import input, render, ui

# HTMLDependency for our demo components JS
_src_dir = Path(__file__).parent
_demo_dep = HTMLDependency(
    name="demo-components",
    version=str(int((_src_dir / "demo_components.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "demo_components.js", "defer": ""},
)


# Subclass shinyjson.render to inject our demo components dependency
class render_demo(shinyjson.render):
    extra_deps = [_demo_dep]


# ---------------------------------------------------------------------------
# Component helpers — thin wrappers around shinyjson.Node that mirror the
# registered JS components in demo_components.js.
# ---------------------------------------------------------------------------
def card(title: str, *children: shinyjson.Node) -> shinyjson.Node:
    return shinyjson.Node(type="Card", props={"title": title}, children=list(children))


def badge(text: str, variant: str = "default") -> shinyjson.Node:
    return shinyjson.Node(type="Badge", props={"text": text, "variant": variant})


def button(label: str, input_id: str, color: str = "#4a90d9") -> shinyjson.Node:
    return shinyjson.Node(
        type="Button", props={"label": label, "input_id": input_id, "color": color}
    )


# ---------------------------------------------------------------------------

ui.page_opts(title="Hello Shinyjson")

ui.h2("Shinyjson Demo")
ui.p("This app demonstrates shinyjson's Python API with reactive updates.")

with ui.layout_sidebar():
    with ui.sidebar():
        ui.input_text("title", "Card Title", value="Hello Shinyjson!")
        ui.input_slider("count", "Badge Count", min=0, max=10, value=3)
        ui.input_select(
            "variant",
            "Badge Variant",
            choices=["default", "success", "warning", "danger", "info"],
            selected="info",
        )

    @render_demo
    def demo_output() -> shinyjson.Node:
        badges = [badge(f"#{i + 1}", input.variant()) for i in range(input.count())]
        return card(
            input.title(),
            *badges,
            button("Click me", "btn_click"),
        )

    ui.h4("Input Values")

    @render.code
    def input_values():
        clicks = input.btn_click() if input.btn_click.is_set() else 0
        return (
            f"Card Title:   {input.title()!r}\n"
            f"Badge Count:  {input.count()}\n"
            f"Badge Variant: {input.variant()}\n"
            f"Button Clicks: {clicks}"
        )
