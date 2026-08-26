from faithful import histogram, waiting
from shiny import Inputs, Outputs, Session
from shinyreact import ReactApp, reactive_output


def server(input: Inputs, output: Outputs, session: Session):
    @reactive_output
    def dist_data():
        return histogram(waiting, input.bins())

    @reactive_output
    def dist_caption():
        n = input.bins()
        return f"{len(waiting)} eruptions in {n} bin{'' if n == 1 else 's'}"


# ReactApp discovers www/ui.js + www/ui.css (Core API) and serves them itself.
app = ReactApp(server)
