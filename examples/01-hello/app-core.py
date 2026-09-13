from faithful import histogram, waiting
from shiny import Inputs, Outputs, Session
from shinyreact import ReactApp, reactive_output


def server(input: Inputs, output: Outputs, session: Session):
    # py-shiny#2497: `Jsonifiable`'s `dict`/`list` arms are invariant, so a
    # `dict` return is not assignable to it. Drop the ignore when that lands.
    @reactive_output  # pyright: ignore[reportArgumentType]
    def dist_data():
        return histogram(waiting, input.bins())

    @reactive_output
    def dist_caption():
        n = input.bins()
        return f"{len(waiting)} eruptions in {n} bin{'' if n == 1 else 's'}"


# ReactApp discovers www/ui.js + www/ui.css (Core API) and serves them itself.
app = ReactApp(server)
