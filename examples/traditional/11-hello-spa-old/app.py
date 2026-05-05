import shinyjsonold as shinyjson
from shiny import App, Inputs, Outputs, Session

app_ui = shinyjson.page_react(
    shinyjson.page_react_dep(js_file="main.js", css_file="styles.css"),
    title="Hello SPA",
)


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def txtout():
        return input.txtin().upper()


app = App(app_ui, server)
