from shiny import Inputs, Outputs, Session, reactive
from shinyreact import ReactApp, reactive_output

INITIAL_DATA = {
    "A": ["Apple", "Apricot"],
    "B": ["Banana", "Blueberry"],
    "C": ["Cherry", "Cranberry"],
}


def server(input: Inputs, output: Outputs, session: Session):
    columns = reactive.value(dict(INITIAL_DATA))

    @reactive.effect
    @reactive.event(input.move_item, ignore_init=True)
    def _handle_move():
        msg = input.move_item()
        item, from_col, to_col = msg["item"], msg["from"], msg["to"]
        data = {k: list(v) for k, v in columns().items()}
        if item in data[from_col]:
            data[from_col].remove(item)
            data[to_col].append(item)
            columns.set(data)

    @reactive_output
    def column_data():
        return columns()


# ReactApp finds www/index.html, serves it as-is with Shiny's and shinyreact's
# tags inserted at the placeholder, and mounts www/ at / so the document's
# ui.js / ui.css resolve.
app = ReactApp(server)
