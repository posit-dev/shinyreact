from shiny import App, Inputs, Outputs, Session, reactive
from shinyreact import page_react_html, reactive_output

app_ui = page_react_html()  # serves www/index.html (Core API)


def server(input: Inputs, output: Outputs, session: Session):
    @reactive.calc
    def greeting():
        name = input.name()
        return name if name else "World"

    @reactive_output
    def txtout_title():
        return f"Hello, {greeting()}!"

    @reactive_output
    def txtout_count():
        return input.click_count()


app = App(app_ui, server)
