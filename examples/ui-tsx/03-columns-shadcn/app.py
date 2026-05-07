from shiny import reactive
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()

INITIAL_DATA = {
    "A": ["Apple", "Apricot"],
    "B": ["Banana", "Blueberry"],
    "C": ["Cherry", "Cranberry"],
}

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
