"""shinymui — `ui.tsx` pattern example.

The page shell, headings, and section layout live in `src/App.jsx` as
hand-written React. Each section uses a `<div class="shinyreact-output" />`
mount point that consumes a server-side `@shinymui_output` returning a
`shinymui.Node`. The registered shinymui catalog (loaded via
`shinymui.dep()`) renders those specs via shinyreact's existing
OutputBinding.

The paired `examples/app-py/14-shinymui/` example produces the same UI
through the `app.py` pattern.

`shinymui_output` is a tiny subclass of `shinyreact.reactive_output` per
RFC §4.4: its only purpose is to attach `shinymui.dep()` to the
auto-discovered HTMLDependencies so `set_react_page()` includes the
bundle.
"""

import shinymui
import shinyreact
from htmltools import Tag
from shiny import reactive
from shiny.express import input
from shinyreact import reactive_output, set_react_page, ui_output

set_react_page()


class shinymui_output(reactive_output):
    """`reactive_output` variant that attaches `shinymui.dep()` to the page.

    `set_react_page()` discovers HTMLDependencies by calling
    `auto_output_ui()` on every Renderer in the app. Returning a `ui_output`
    that carries the shinymui dep contributes the dep to the page (Shiny
    dedupes by name+version so multiple renderers sharing the same dep is
    fine).
    """

    def auto_output_ui(self) -> Tag:
        return ui_output(self.output_id, extra_deps=[shinymui.dep()])


SAMPLE_ROWS = [
    {"id": 1, "name": "Alice", "age": 30, "score": 85},
    {"id": 2, "name": "Bob", "age": 25, "score": 92},
    {"id": 3, "name": "Carol", "age": 42, "score": 78},
    {"id": 4, "name": "Dave", "age": 35, "score": 88},
    {"id": 5, "name": "Eve", "age": 28, "score": 95},
]


@shinymui_output
def controls_card():
    name = input.name() or "World"
    threshold = input.age() or 0
    clicks = input.btn1() or 0
    return shinymui.card(
        "Controls",
        shinymui.text_field(input_id="name", label="Name", default_value="World"),
        shinymui.slider(
            input_id="age",
            label="Min age filter",
            default_value=25,
            min=0,
            max=50,
        ),
        shinymui.button("Click me", input_id="btn1", start_icon="TouchApp"),
        shinyreact.Node(
            type="div",
            props={
                "children": f"Hello, {name}! Age filter: {threshold}. Clicks: {clicks}."
            },
        ),
    )


@shinymui_output
def data_card():
    return shinymui.card(
        "Filtered data (DataGrid)",
        shinymui.data_grid(output_id="grid1", height=300),
    )


@reactive.calc
def _filtered_rows():
    threshold = input.age() or 0
    return [r for r in SAMPLE_ROWS if r["age"] >= threshold]


@shinymui_output
def grid1():
    return {
        "rows": _filtered_rows(),
        "columns": [
            {"field": "name", "headerName": "Name", "width": 150},
            {"field": "age", "headerName": "Age", "width": 100},
            {"field": "score", "headerName": "Score", "width": 100},
        ],
    }
