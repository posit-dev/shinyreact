from pathlib import Path

import shinyjsonold as shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, module, reactive

_src_dir = Path(__file__).parent
_modules_dep = HTMLDependency(
    name="modules-example",
    version=str(int((_src_dir / "modules.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "modules.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui_output("main", extra_deps=[_modules_dep])


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------
def app_layout(title: str, subtitle: str, *children: shinyjson.Node) -> shinyjson.Node:
    return shinyjson.Node(
        type="AppLayout",
        props={"title": title, "subtitle": subtitle},
        children=list(children),
    )


def widgets_grid(*children: shinyjson.Node) -> shinyjson.Node:
    return shinyjson.Node(type="WidgetsGrid", children=list(children))


def module_counter(namespace: str, label: str) -> shinyjson.Node:
    return shinyjson.Node(
        type="ModuleCounter",
        props={"namespace": namespace, "label": label},
    )


def info_section() -> shinyjson.Node:
    return shinyjson.Node(type="InfoSection")


# Module server function
@module.server
def counter_module_server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def serverCount():
        """Echo the count value from the server"""
        if input.count() is not None:
            return input.count()
        return 0

    @shinyjson.render
    def serverDoubled():
        """Double the count value and send to client"""
        if input.count() is not None:
            return input.count() * 2
        return 0

    @reactive.effect
    async def send_notification():
        """Send notification message every 5 counts"""
        count = input.count()
        if count is not None and count > 0 and count % 5 == 0:
            await shinyjson.post_message(
                session,
                "notification",
                {"message": f"Milestone reached: {count}"},
            )


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def main():
        return app_layout(
            "Shiny Module Namespace Demo",
            "Three independent counter widgets, each in its own namespace",
            widgets_grid(
                module_counter("counter1", "Counter 1"),
                module_counter("counter2", "Counter 2"),
                module_counter("counter3", "Counter 3"),
            ),
            info_section(),
        )

    # Initialize three independent module servers
    counter_module_server("counter1")
    counter_module_server("counter2")
    counter_module_server("counter3")


app = App(app_ui, server)
