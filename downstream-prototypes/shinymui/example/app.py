"""shinymui prototype example app.

Exercises all 5 components in one page. This is the integration test for the
prototype — if every interaction below works, the conventions hold.
"""

import shinymui
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[shinymui.dep()])


SAMPLE_ROWS = [
    {"id": 1, "name": "Alice", "age": 30, "score": 85},
    {"id": 2, "name": "Bob", "age": 25, "score": 92},
    {"id": 3, "name": "Carol", "age": 42, "score": 78},
    {"id": 4, "name": "Dave", "age": 35, "score": 88},
    {"id": 5, "name": "Eve", "age": 28, "score": 95},
]


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        name = input.name() or "World"
        age = input.age() or 0
        clicks = input.btn1() or 0
        return shinyreact.Node(
            type="div",
            props={
                "style": {
                    "padding": "16px",
                    "fontFamily": "sans-serif",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "16px",
                    "maxWidth": "800px",
                    "margin": "0 auto",
                }
            },
            children=[
                shinyreact.Node(type="h1", props={"children": "shinymui prototype"}),
                shinymui.card(
                    "Controls",
                    shinymui.text_field(
                        input_id="name", label="Name", default_value="World"
                    ),
                    shinymui.slider(
                        input_id="age",
                        label="Min age filter",
                        default_value=25,
                        min=0,
                        max=50,
                    ),
                    shinymui.button(
                        "Click me", input_id="btn1", start_icon="TouchApp"
                    ),
                    shinyreact.Node(
                        type="div",
                        props={
                            "children": f"Hello, {name}! Age filter: {age}. Clicks: {clicks}."
                        },
                    ),
                ),
                shinymui.card(
                    "Filtered data (DataGrid)",
                    shinymui.data_grid(output_id="grid1", height=300),
                ),
            ],
        )

    @shinyreact.reactive_output
    def grid1():
        threshold = input.age() or 0
        rows = [r for r in SAMPLE_ROWS if r["age"] >= threshold]
        return {
            "rows": rows,
            "columns": [
                {"field": "name", "headerName": "Name", "width": 150},
                {"field": "age", "headerName": "Age", "width": 100},
                {"field": "score", "headerName": "Score", "width": 100},
            ],
        }


app = App(app_ui, server)
