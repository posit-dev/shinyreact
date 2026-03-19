from pathlib import Path

import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, module, reactive

_modules_dep = HTMLDependency(
    name="modules-example",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "modules.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("main", extra_deps=[_modules_dep])


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
        return shinyjson.Spec(
            root="app",
            elements={
                "app": shinyjson.Element(type="App", props={}),
            },
        )

    # Initialize three independent module servers
    counter_module_server("counter1")
    counter_module_server("counter2")
    counter_module_server("counter3")


app = App(app_ui, server)
