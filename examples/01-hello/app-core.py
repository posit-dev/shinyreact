from faithful import histogram, waiting
from shiny import App, Inputs, Outputs, Session
from shinyreact import page_react_html, reactive_output

app_ui = page_react_html()  # serves www/index.html (Core API)


def server(input: Inputs, output: Outputs, session: Session):
    @reactive_output
    def dist_data():
        return histogram(waiting, input.bins())

    @reactive_output
    def dist_caption():
        n = input.bins()
        return f"{len(waiting)} eruptions in {n} bin{'' if n == 1 else 's'}"


app = App(app_ui, server)
