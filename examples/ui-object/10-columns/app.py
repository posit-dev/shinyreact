from shiny import App, Inputs, Outputs, Session, reactive, render, ui

app_ui = ui.page_fluid(
    ui.h2("Move Items Between Columns"),
    ui.row(
        ui.column(4, ui.h4("Column A"), ui.output_ui("col_a")),
        ui.column(4, ui.h4("Column B"), ui.output_ui("col_b")),
        ui.column(4, ui.h4("Column C"), ui.output_ui("col_c")),
    ),
)

INITIAL_DATA = {
    "A": ["Apple", "Apricot"],
    "B": ["Banana", "Blueberry"],
    "C": ["Cherry", "Cranberry"],
}

COLUMNS = ["A", "B", "C"]


def server(input: Inputs, output: Outputs, session: Session):
    columns = reactive.value(dict(INITIAL_DATA))
    _observers: list[reactive.Effect_] = []

    def _move_item(item: str, from_col: str, to_col: str):
        data = {k: list(v) for k, v in columns().items()}
        if item in data[from_col]:
            data[from_col].remove(item)
            data[to_col].append(item)
            columns.set(data)

    def _btn_id(item: str, col: str, direction: str) -> str:
        safe = item.lower().replace(" ", "_")
        return f"move_{safe}_{col}_{direction}"

    @reactive.effect
    def _setup_observers():
        # Destroy previous observers
        for obs in _observers:
            obs.destroy()
        _observers.clear()

        data = columns()
        for col in COLUMNS:
            col_idx = COLUMNS.index(col)
            for item in data[col]:
                if col_idx > 0:
                    _make_observer(item, col, COLUMNS[col_idx - 1], "left")
                if col_idx < len(COLUMNS) - 1:
                    _make_observer(item, col, COLUMNS[col_idx + 1], "right")

    def _make_observer(item: str, from_col: str, to_col: str, direction: str):
        btn_id = _btn_id(item, from_col, direction)

        @reactive.effect
        @reactive.event(input[btn_id], ignore_init=True)
        def _obs():
            _move_item(item, from_col, to_col)

        _observers.append(_obs)

    def _render_column(col_name: str):
        data = columns()
        items = data[col_name]
        col_idx = COLUMNS.index(col_name)

        elements = []
        for item in items:
            buttons = []
            if col_idx > 0:
                btn_id = _btn_id(item, col_name, "left")
                buttons.append(
                    ui.input_action_button(
                        btn_id, "←", class_="btn-sm btn-outline-secondary"
                    )
                )
            if col_idx < len(COLUMNS) - 1:
                btn_id = _btn_id(item, col_name, "right")
                buttons.append(
                    ui.input_action_button(
                        btn_id, "→", class_="btn-sm btn-outline-secondary"
                    )
                )
            elements.append(
                ui.div(
                    ui.span(item, style="margin-right: 0.5rem;"),
                    *buttons,
                    class_="d-flex align-items-center mb-2 p-2 border rounded",
                )
            )

        return ui.div(*elements) if elements else ui.p("(empty)", class_="text-muted")

    @render.ui
    def col_a():
        return _render_column("A")

    @render.ui
    def col_b():
        return _render_column("B")

    @render.ui
    def col_c():
        return _render_column("C")


app = App(app_ui, server)
