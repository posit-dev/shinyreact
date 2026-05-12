from pathlib import Path

import shinyreact
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, module

_src_dir = Path(__file__).parent
_dep = HTMLDependency(
    name="module-counter-fixture",
    version=str(int((_src_dir / "modules.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "modules.js", "defer": ""},
)

app_ui = shinyreact.ui_output("main", extra_deps=[_dep])


@module.server
def counter_server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def serverCount():
        return input.count() or 0


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        return shinyreact.Node(
            type="Container",
            children=[
                shinyreact.Node(type="Counter", props={"namespace": "a"}),
                shinyreact.Node(type="Counter", props={"namespace": "b"}),
            ],
        )

    counter_server("a")
    counter_server("b")


app = App(app_ui, server)
