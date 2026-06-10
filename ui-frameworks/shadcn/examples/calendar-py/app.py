"""Calendar demo — single date picker, value crosses the wire as an ISO string."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py"))

import shadcn as sc
import shinyreact
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("demo", extra_deps=[sc._dep()]),
        style="max-width:420px; margin:2rem auto; padding:0 1rem;",
    )
)


def server(input, output, session):
    @shinyreact.render_react
    def demo():
        raw = input.pick_date() if "pick_date" in input else None
        if raw:
            d = date.fromisoformat(raw)
            msg = f"You picked {d:%A, %B %d, %Y}"
        else:
            msg = "No date selected yet."

        return sc.card(
            sc.calendar("pick_date", selected="2026-06-10"),
            sc.separator(),
            sc.alert(msg, title="Selected date"),
            title="Calendar",
        )


app = App(app_ui, server)
