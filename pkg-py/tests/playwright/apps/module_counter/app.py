from shiny import Inputs, Outputs, Session, module
from shiny.express import render  # noqa: F401  # marks this file as Shiny Express
from shinyreact import reactive_output, set_react_page

set_react_page()


@module.server
def counter_server(input: Inputs, output: Outputs, session: Session):
    @reactive_output
    def serverCount():
        return input.count() or 0


counter_server("a")
counter_server("b")
