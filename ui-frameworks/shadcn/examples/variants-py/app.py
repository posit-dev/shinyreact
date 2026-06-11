"""Variants gallery — every component and its variants/sizes laid out in rows.

A visual reference sheet: each row shows one component across all its variants,
sizes, or states, plus a couple of className customizations (changed colors/size).
Run: shiny run ui-frameworks/shadcn/examples/variants-py/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py"))

import shadcn as sc
import shinyreact
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("variants", extra_deps=[sc._dep()]),
        style="max-width:760px; margin:2.5rem auto; padding:0 1rem;",
    ),
    title="shadcn × shinyreact — variants",
)


def _row(label: str, *items: object) -> ui.Tag:
    """A labeled row: caption above, variations wrapping below."""
    return ui.div(
        ui.div(label, class_="text-sm font-medium"),
        ui.div(*items, class_="flex flex-wrap gap-2 items-center"),
        class_="flex flex-col gap-2",
    )


def _section(*rows: object) -> ui.Tag:
    return ui.div(*rows, class_="flex flex-col gap-4")


def server(input, output, session):
    @shinyreact.render_react
    def variants():
        return sc.card(
            ui.div(
                ui.div("Variants & sizes", class_="text-lg font-semibold"),
                ui.div(
                    "Every component across its variants, sizes, and states.",
                    class_="text-sm text-muted-foreground",
                ),
                class_="flex flex-col gap-1",
            ),
            _section(
                _row(
                    "Button · variants",
                    sc.button("b_default", "Default"),
                    sc.button("b_secondary", "Secondary", variant="secondary"),
                    sc.button("b_destructive", "Destructive", variant="destructive"),
                    sc.button("b_outline", "Outline", variant="outline"),
                    sc.button("b_ghost", "Ghost", variant="ghost"),
                    sc.button("b_link", "Link", variant="link"),
                ),
                _row(
                    "Button · sizes",
                    sc.button("s_sm", "Small", size="sm"),
                    sc.button("s_default", "Default", size="default"),
                    sc.button("s_lg", "Large", size="lg"),
                ),
                _row(
                    "Button · custom (className)",
                    sc.button(
                        "c_color", "Custom color", class_="bg-sky-600 hover:bg-sky-700"
                    ),
                    sc.button(
                        "c_round", "Pill", variant="outline", class_="rounded-full"
                    ),
                ),
            ),
            sc.separator(),
            _row(
                "Badge · variants",
                sc.badge("default"),
                sc.badge("secondary", variant="secondary"),
                sc.badge("destructive", variant="destructive"),
                sc.badge("outline", variant="outline"),
                sc.badge("ghost", variant="ghost"),
                sc.badge("link", variant="link"),
                sc.badge("custom", class_="bg-emerald-600 text-white"),
            ),
            sc.separator(),
            _row(
                "Switch · states",
                sc.switch("sw_off", label="Off"),
                sc.switch("sw_on", label="On", checked=True),
            ),
            _row(
                "Checkbox · states",
                sc.checkbox("cb_off", label="Unchecked"),
                sc.checkbox("cb_on", label="Checked", checked=True),
            ),
            sc.separator(),
            ui.div(
                ui.div("Alert · variants", class_="text-sm font-medium"),
                sc.alert("A neutral, informational message.", title="Heads up"),
                sc.alert(
                    "Something needs your attention.",
                    title="Error",
                    variant="destructive",
                ),
                class_="flex flex-col gap-2",
            ),
            title="Component variants",
        )


app = App(app_ui, server)
