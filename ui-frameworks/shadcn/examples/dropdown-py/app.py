"""Dropdown menu demo — data-driven compound component with mixed event + state."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py" / "src"))

import shinyreact
import shinyshadcn as sc
from shiny import App, reactive, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("demo", extra_deps=[sc._dep()]),
        style="max-width:520px; margin:2rem auto; padding:0 1rem;",
    )
)


def server(input, output, session):
    last_action = reactive.value("none")

    @reactive.effect
    @reactive.event(input.menu_action, ignore_init=True)
    def _():
        last_action.set(input.menu_action()["value"])

    @shinyreact.render_react
    def demo():
        action = last_action()
        show_toolbar = input.show_toolbar() if "show_toolbar" in input else True
        show_url = input.show_url() if "show_url" in input else False

        return sc.card(
            sc.dropdown_menu(
                "menu_action",
                sc.menu_label("My Account"),
                sc.menu_separator(),
                sc.menu_item("profile", "Profile"),
                sc.menu_item("billing", "Billing"),
                sc.menu_submenu(
                    "More tools",
                    sc.menu_item("import", "Import"),
                    sc.menu_item("export", "Export"),
                ),
                sc.menu_separator(),
                sc.menu_checkbox("show_toolbar", "Show toolbar", checked=True),
                sc.menu_checkbox("show_url", "Show full URLs"),
                sc.menu_separator(),
                sc.menu_item("logout", "Log out", variant="destructive"),
                trigger_label="Open menu",
            ),
            sc.separator(),
            sc.alert(f"Last action: {action}", title="Event input"),
            ui.div(
                sc.badge(f"toolbar: {show_toolbar}"),
                sc.badge(f"urls: {show_url}", variant="secondary"),
                class_="flex gap-2",
            ),
            title="Dropdown menu",
        )


app = App(app_ui, server)
