import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.page_react(
    shinyreact.page_react_dep(js_file="main.js", css_file="styles.css"),
    title="Hello SPA",
)


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def txtout():
        return input.txtin().upper()


app = App(app_ui, server)
