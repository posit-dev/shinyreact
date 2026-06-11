"""Component gallery — every shadcn x shinyreact component in one showcase.

Each component sits in a labeled preview box (like shadcn's own docs), grouped
into tabs. Every panel is live-wired so you can interact and watch values update.
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
        style="max-width:720px; margin:2.5rem auto; padding:0 1rem;",
    ),
    title="shadcn × shinyreact gallery",
)


def _demo(label: str, *children: object) -> ui.Tag:
    """A labeled preview box wrapping one component (shadcn-docs style)."""
    return ui.div(
        ui.div(
            label,
            class_="text-xs font-medium uppercase tracking-wide text-muted-foreground",
        ),
        ui.div(*children, class_="flex flex-col gap-3"),
        class_="rounded-lg border p-4 flex flex-col gap-3",
    )


def _grid(*demos: object) -> ui.Tag:
    return ui.div(*demos, class_="grid grid-cols-2 gap-4")


def _stack(*demos: object) -> ui.Tag:
    return ui.div(*demos, class_="flex flex-col gap-4")


def server(input, output, session):
    last_menu = reactive.value("none")

    @reactive.effect
    @reactive.event(input.menu_action, ignore_init=True)
    def _on_menu():
        last_menu.set(input.menu_action()["value"])

    @reactive.effect
    @reactive.event(input.toast_btn, ignore_init=True)
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
        when = f"{date.fromisoformat(picked):%b %d, %Y}" if picked else "—"

        return _stack(
            _demo("Text input", sc.text_input("g_name", placeholder="Your name…")),
            _demo(
                "Select",
                sc.select(
                    "g_fruit",
                    choices=[
                        {"value": "apple", "label": "Apple"},
                        {"value": "banana", "label": "Banana"},
                        {"value": "cherry", "label": "Cherry"},
                    ],
                    selected="apple",
                ),
            ),
            _demo(
                "Slider",
                sc.slider("g_level", min=0, max=100, step=5, value=40, label="Level"),
            ),
            _grid(
                _demo(
                    "Switch", sc.switch("g_notify", label="Notifications", checked=True)
                ),
                _demo("Checkbox", sc.checkbox("g_terms", label="Accept terms")),
            ),
            _demo("Calendar", sc.calendar("g_date")),
            sc.alert(
                f"name={name or '∅'} · fruit={fruit} · level={level} · "
                f"notify={notify} · terms={terms} · date={when}",
                title="Live input values",
            ),
        )

    def display_panel():
        return _stack(
            _demo(
                "Badge",
                ui.div(
                    sc.badge("default"),
                    sc.badge("secondary", variant="secondary"),
                    sc.badge("outline", variant="outline"),
                    class_="flex gap-2 flex-wrap",
                ),
            ),
            _demo(
                "Alert",
                sc.alert("A neutral, informational message.", title="Heads up"),
                sc.alert(
                    "Something needs your attention.",
                    title="Error",
                    variant="destructive",
                ),
            ),
            _demo(
                "Table",
                sc.table(
                    columns=["Name", "Role", "Commits"],
                    rows=[
                        ["Ada", "Author", 128],
                        ["Linus", "Maintainer", 4096],
                        ["Grace", "Reviewer", 64],
                    ],
                    caption="Contributor activity",
                ),
            ),
        )

    def actions_panel():
        clicks = input.g_btn() if "g_btn" in input else 0
        return _stack(
            _grid(
                _demo("Button", sc.button("g_btn", "Click me")),
                _demo(
                    "Dropdown menu",
                    sc.dropdown_menu(
                        "menu_action",
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
                        trigger_label="Open menu",
                    ),
                ),
                _demo(
                    "Popover",
                    sc.popover(
                        "g_pop",
                        sc.badge("Inside a popover"),
                        sc.text_input("g_pop_text", placeholder="Type here…"),
                        trigger_label="Open popover",
                    ),
                ),
                _demo(
                    "Dialog",
                    sc.dialog(
                        "g_dialog",
                        sc.text_input("g_dialog_name", label="Name"),
                        sc.slider(
                            "g_dialog_age", min=18, max=99, value=30, label="Age"
                        ),
                        trigger_label="Open dialog",
                        title="Edit profile",
                        description="Make changes and close when done.",
                    ),
                ),
            ),
            sc.alert(
                f"button clicks={clicks} · last menu action={last_menu()}",
                title="Live action state",
            ),
        )

    def feedback_panel():
        return _stack(
            sc.toaster(),  # host — renders nothing until a toast is pushed
            _demo(
                "Toast (server push)",
                sc.alert("Click below; the server pushes a toast notification."),
                sc.button("toast_btn", "Show toast"),
            ),
        )

    # ---- assemble ---------------------------------------------------------

    @shinyreact.render_react
    def gallery():
        active = input.gallery_tabs() if "gallery_tabs" in input else "inputs"
        return sc.card(
            ui.div(
                ui.div("Component Gallery", class_="text-lg font-semibold"),
                ui.div(
                    "shadcn × shinyreact — every component, live-wired.",
                    class_="text-sm text-muted-foreground",
                ),
                class_="flex flex-col gap-1",
            ),
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
            ui.div(
                sc.badge(f"viewing: {active}", variant="secondary"),
                class_="flex",
            ),
        )


app = App(app_ui, server)
