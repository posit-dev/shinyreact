"""Overlay components demo — Dialog, Popover, and Radix Select."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py"))

import shadcn as sc
import shinyreact
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("demo", extra_deps=[sc._dep()]),
        style="max-width:520px; margin:2rem auto; padding:0 1rem;",
    )
)


def server(input, output, session):
    @shinyreact.render_react
    def demo():
        color = input.color() if "color" in input else "blue"
        confirm_clicks = input.confirm_btn() if "confirm_btn" in input else 0

        status = (
            f"Confirmed with {color}!" if confirm_clicks > 0 else "No confirmation yet."
        )
        color_variant = {"blue": "default", "green": "secondary", "red": "outline"}.get(
            color, "outline"
        )

        return sc.card(
            # Radix Select — real dropdown with checkmark and keyboard nav
            sc.select(
                "color",
                choices=[
                    {"value": "blue", "label": "Blue"},
                    {"value": "green", "label": "Green"},
                    {"value": "red", "label": "Red"},
                ],
                selected="blue",
                label="Favorite color",
            ),
            sc.badge(color, variant=color_variant),
            sc.separator(),
            # Popover — floating panel with child content
            sc.popover(
                "color_popover",
                sc.alert("Popover is open!", title="Info"),
                sc.badge(f"Color is {color}"),
                trigger_label="Color details",
            ),
            sc.separator(),
            # Dialog — modal with focus trap, child content, Close button
            sc.dialog(
                "info_dialog",
                sc.text_input("username", placeholder="Your name…", label="Name"),
                sc.slider("age", min=18, max=100, step=1, value=25, label="Age"),
                sc.button("confirm_btn", "Confirm"),
                trigger_label="Edit profile",
                title="Edit your profile",
                description="Update your details below.",
            ),
            sc.alert(status, title="Status"),
            title="Overlay components",
        )


app = App(app_ui, server)
