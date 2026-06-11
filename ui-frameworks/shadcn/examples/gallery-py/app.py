"""Component gallery — every shadcn × shinyreact component in one app.

Organized with Tabs into Inputs / Display / Actions & Overlays / Feedback.
Each panel is live-wired so you can interact and watch the reactive values update.
Run: shiny run ui-frameworks/shadcn/examples/gallery-py/app.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py"))

import shadcn as sc
import shinyreact
from shiny import App, reactive, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("gallery", extra_deps=[sc._dep()]),
        # This outer div is page chrome (rendered by htmltools, not React), so a
        # string style is fine here. Inside render_react, use class_ with Tailwind
        # utilities instead — React rejects string styles (error #62).
        style="max-width:640px; margin:2rem auto; padding:0 1rem;",
    ),
    title="shadcn × shinyreact gallery",
)


def server(input, output, session):
    last_menu = reactive.value("none")

    @reactive.effect
    @reactive.event(input.g_menu, ignore_init=True)
    def _on_menu():
        last_menu.set(input.g_menu()["value"])

    @reactive.effect
    @reactive.event(input.g_toast, ignore_init=True)
    async def _on_toast():
        await sc.toast(
            session,
            "Saved!",
            description="Your settings were updated.",
            type="success",
        )

    # ---- panels -----------------------------------------------------------

    def inputs_panel():
        name = input.g_name() if "g_name" in input else ""
        fruit = input.g_fruit() if "g_fruit" in input else "apple"
        level = input.g_level() if "g_level" in input else 40
        notify = input.g_notify() if "g_notify" in input else True
        terms = input.g_terms() if "g_terms" in input else False
        picked = input.g_date() if "g_date" in input else None
        when = f"{date.fromisoformat(picked):%b %d, %Y}" if picked else "none"

        return ui.div(
            sc.text_input("g_name", placeholder="Your name…", label="Text input"),
            sc.select(
                "g_fruit",
                choices=[
                    {"value": "apple", "label": "Apple"},
                    {"value": "banana", "label": "Banana"},
                    {"value": "cherry", "label": "Cherry"},
                ],
                selected="apple",
                label="Select",
            ),
            sc.slider("g_level", min=0, max=100, step=5, value=40, label="Slider"),
            sc.switch("g_notify", label="Switch — notifications", checked=True),
            sc.checkbox("g_terms", label="Checkbox — accept terms"),
            sc.calendar("g_date"),
            sc.separator(),
            sc.alert(
                f"name={name or '∅'} · fruit={fruit} · level={level} · "
                f"notify={notify} · terms={terms} · date={when}",
                title="Live input values",
            ),
            class_="flex flex-col gap-4",
        )

    def display_panel():
        return ui.div(
            ui.div(
                sc.badge("default"),
                sc.badge("secondary", variant="secondary"),
                sc.badge("outline", variant="outline"),
                class_="flex gap-2",
            ),
            sc.alert("A neutral, informational message.", title="Default alert"),
            sc.alert(
                "Something needs your attention.",
                title="Destructive alert",
                variant="destructive",
            ),
            sc.separator(),
            sc.table(
                columns=["Name", "Role", "Commits"],
                rows=[
                    ["Ada", "Author", 128],
                    ["Linus", "Maintainer", 4096],
                    ["Grace", "Reviewer", 64],
                ],
                caption="Table — contributor activity",
            ),
            class_="flex flex-col gap-4",
        )

    def actions_panel():
        clicks = input.g_btn() if "g_btn" in input else 0
        return ui.div(
            ui.div(
                sc.button("g_btn", "Button"),
                sc.dropdown_menu(
                    "g_menu",
                    sc.menu_label("Actions"),
                    sc.menu_item("edit", "Edit"),
                    sc.menu_item("duplicate", "Duplicate"),
                    sc.menu_submenu(
                        "Move to",
                        sc.menu_item("inbox", "Inbox"),
                        sc.menu_item("archive", "Archive"),
                    ),
                    sc.menu_separator(),
                    sc.menu_item("delete", "Delete", variant="destructive"),
                    trigger_label="Dropdown menu",
                ),
                class_="flex gap-2",
            ),
            ui.div(
                sc.popover(
                    "g_pop",
                    sc.badge("Inside a popover"),
                    sc.text_input("g_pop_text", placeholder="Type here…"),
                    trigger_label="Popover",
                ),
                sc.dialog(
                    "g_dialog",
                    sc.text_input("g_dialog_name", label="Name"),
                    sc.slider("g_dialog_age", min=18, max=99, value=30, label="Age"),
                    trigger_label="Dialog",
                    title="Edit profile",
                    description="Make changes and close when done.",
                ),
                class_="flex gap-2",
            ),
            sc.separator(),
            sc.alert(
                f"button clicks={clicks} · last menu action={last_menu()}",
                title="Live action state",
            ),
            class_="flex flex-col gap-4",
        )

    def feedback_panel():
        return ui.div(
            sc.toaster(),  # host — renders nothing until a toast is pushed
            sc.alert(
                "Click the button to have the server push a toast notification.",
                title="Toast (server push)",
            ),
            sc.button("g_toast", "Show toast"),
            class_="flex flex-col gap-4",
        )

    # ---- assemble ---------------------------------------------------------

    @shinyreact.render_react
    def gallery():
        active = input.gallery_tabs() if "gallery_tabs" in input else "inputs"
        return sc.card(
            sc.tabs(
                "gallery_tabs",
                [
                    sc.tab("inputs", "Inputs"),
                    sc.tab("display", "Display"),
                    sc.tab("actions", "Actions"),
                    sc.tab("feedback", "Feedback"),
                ],
                inputs_panel(),
                display_panel(),
                actions_panel(),
                feedback_panel(),
                selected="inputs",
            ),
            sc.separator(),
            ui.div(
                sc.badge(f"viewing: {active}", variant="secondary"),
                class_="flex",
            ),
            title="shadcn × shinyreact — Component Gallery",
        )


app = App(app_ui, server)
