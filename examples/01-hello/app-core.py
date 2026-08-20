from faithful import histogram, waiting
from shiny import App, Inputs, Outputs, Session
from shinyreact import page_react, reactive_output

app_ui = page_react()  # discovers www/ui.js + www/ui.css (Core API)


def server(input: Inputs, output: Outputs, session: Session):
    @reactive_output
    def dist_data():
        return histogram(waiting, input.bins())

    @reactive_output
    def dist_caption():
        n = input.bins()
        return f"{len(waiting)} eruptions in {n} bin{'' if n == 1 else 's'}"


# page_react() serves ui.js/ui.css itself (an mtime-versioned dependency), so
# no static_assets mount is needed for them.
app = App(app_ui, server)
