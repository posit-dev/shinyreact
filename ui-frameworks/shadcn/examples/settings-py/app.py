"""User-preferences panel — showcases all 10 shadcn components."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py" / "src"))

import shinyreact
import shinyshadcn as sc
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("prefs", extra_deps=[sc._dep()]),
        style="max-width:440px; margin:2rem auto; padding:0 1rem;",
    )
)


def server(input, output, session):
    @shinyreact.render_react
    def prefs():
        theme = input.theme() if "theme" in input else "system"
        saves = input.save_btn() if "save_btn" in input else 0

        theme_variant = {
            "light": "default",
            "dark": "secondary",
            "system": "outline",
        }.get(theme, "outline")
        status = (
            f"Saved {saves} time{'s' if saves != 1 else ''}."
            if saves > 0
            else "Make changes and save."
        )

        return sc.card(
            sc.text_input(
                "display_name", placeholder="e.g. Ada Lovelace", label="Display name"
            ),
            sc.select(
                "theme",
                choices=[
                    {"value": "light", "label": "Light"},
                    {"value": "dark", "label": "Dark"},
                    {"value": "system", "label": "System default"},
                ],
                selected="system",
                label="Color theme",
            ),
            sc.badge(theme, variant=theme_variant),
            sc.separator(),
            sc.slider(
                "font_size", min=10, max=20, step=1, value=14, label="Font size (px)"
            ),
            sc.switch("notifications", label="Enable notifications", checked=True),
            sc.checkbox("newsletter", label="Subscribe to newsletter"),
            sc.separator(),
            sc.button("save_btn", "Save preferences"),
            sc.alert(status, title="Status"),
            title="User Preferences",
        )


app = App(app_ui, server)
