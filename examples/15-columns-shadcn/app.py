from pathlib import Path

from shiny import reactive
from shinyjson import SpaApp, render_json

_src_dir = Path(__file__).parent

INITIAL_DATA = {
    "A": ["Apple", "Apricot"],
    "B": ["Banana", "Blueberry"],
    "C": ["Cherry", "Cranberry"],
}


def server(input, output, session):  # noqa: ARG001
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

    @render_json
    def column_data():
        return columns()


app = SpaApp(_src_dir / "www", server)
