from pathlib import Path

from htmltools import HTMLDependency
from shiny.express import input, ui

import shinyjson

# HTMLDependency for our demo components JS
_demo_dep = HTMLDependency(
    name="demo-components",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "demo_components.js"},
)


# Subclass shinyjson.render to inject our demo components dependency
class render_demo(shinyjson.render):
    extra_deps = [_demo_dep]


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
    def demo_output() -> shinyjson.Spec:
        # Build a nested element tree
        elements: dict[str, shinyjson.Element] = {}

        # Create badge elements based on slider count
        badge_keys: list[str] = []
        for i in range(input.count()):
            key = f"badge_{i}"
            badge_keys.append(key)
            elements[key] = shinyjson.Element(
                type="Badge",
                props={
                    "text": f"#{i + 1}",
                    "variant": input.variant(),
                },
            )

        # Create a button
        elements["btn"] = shinyjson.Element(
            type="Button",
            props={"label": "Click me", "color": "#4a90d9"},
        )

        # Create a card containing the badges and button
        elements["card"] = shinyjson.Element(
            type="Card",
            props={"title": input.title()},
            children=badge_keys + ["btn"],
        )

        return shinyjson.Spec(root="card", elements=elements)
