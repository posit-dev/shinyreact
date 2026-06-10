"""Tabs + Table demo — hybrid collection-with-children and data display."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py"))

import shadcn as sc
import shinyreact
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("demo", extra_deps=[sc._dep()]),
        style="max-width:560px; margin:2rem auto; padding:0 1rem;",
    )
)


def server(input, output, session):
    @shinyreact.render_react
    def demo():
        active = input.main_tabs() if "main_tabs" in input else "overview"

        return sc.card(
            sc.tabs(
                "main_tabs",
                [
                    sc.tab("overview", "Overview"),
                    sc.tab("data", "Data"),
                    sc.tab("settings", "Settings"),
                ],
                # panel 1 — overview
                sc.alert("This is the overview panel.", title="Overview"),
                # panel 2 — data (a table)
                sc.table(
                    columns=["Name", "Role", "Commits"],
                    rows=[
                        ["Ada", "Author", 128],
                        ["Linus", "Maintainer", 4096],
                        ["Grace", "Reviewer", 64],
                    ],
                    caption="Contributor activity",
                ),
                # panel 3 — settings
                sc.switch("setting_dark", label="Dark mode"),
                selected="overview",
            ),
            sc.separator(),
            sc.badge(f"active tab: {active}"),
            title="Tabs + Table",
        )


app = App(app_ui, server)
