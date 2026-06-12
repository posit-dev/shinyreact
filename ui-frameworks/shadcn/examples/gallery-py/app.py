"""Component gallery — every shadcn x shinyreact component in one showcase.

Each component sits in a labeled preview box (like shadcn's own docs), grouped
into tabs. Every panel is live-wired so you can interact and watch values update.
Run: shiny run ui-frameworks/shadcn/examples/gallery-py/app.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py" / "src"))

import shinyreact
import shinyshadcn as sc
from shiny import App, reactive, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("gallery", extra_deps=[sc._dep()]),
        style="max-width:800px; margin:2.5rem auto; padding:0 1rem;",
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
    last_menubar = reactive.value("—")
    last_ctx = reactive.value("—")

    @reactive.effect
    @reactive.event(input.menu_action, ignore_init=True)
    def _on_menu():
        last_menu.set(input.menu_action()["value"])

    @reactive.effect
    @reactive.event(input.g_menubar, ignore_init=True)
    def _on_menubar():
        sel = input.g_menubar()
        last_menubar.set(f"{sel['menu']} → {sel['value']}")

    @reactive.effect
    @reactive.event(input.g_ctx, ignore_init=True)
    def _on_ctx():
        last_ctx.set(input.g_ctx()["value"])

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
        otp = input.g_otp() if "g_otp" in input else ""
        page = input.g_page() if "g_page" in input else 1

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
                    "Switch",
                    sc.switch("g_notify", label="Notifications", checked=True),
                ),
                _demo("Checkbox", sc.checkbox("g_terms", label="Accept terms")),
            ),
            _demo("Calendar", sc.calendar("g_date")),
            _demo(
                "Radio group",
                sc.radio_group(
                    "g_fruit_radio",
                    choices=["Apple", "Banana", "Cherry"],
                    selected="Apple",
                ),
            ),
            _demo(
                "OTP input",
                sc.input_otp("g_otp", length=6, separator=True),
            ),
            _demo(
                "Pagination",
                sc.pagination("g_page", total_pages=10, current=1),
            ),
            sc.alert(
                f"name={name or '∅'} · fruit={fruit} · level={level} · "
                f"notify={notify} · terms={terms} · date={when} · "
                f"otp={otp or '∅'} · page={page}",
                title="Live input values",
            ),
        )

    def display_panel():
        return _stack(
            _grid(
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
                    "Tooltip",
                    sc.tooltip(
                        sc.badge("Hover me", variant="secondary"),
                        content="This is a tooltip",
                        side="top",
                    ),
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
                "Hover card",
                sc.hover_card(
                    sc.card(
                        ui.div("@shadcn", class_="font-semibold"),
                        ui.div(
                            "Building component libraries for React.",
                            class_="text-sm text-muted-foreground",
                        ),
                    ),
                    trigger_label="@shadcn",
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
            _demo(
                "Empty state",
                sc.empty(
                    sc.button("empty_btn", "Create item"),
                    title="No items yet",
                    description="Get started by creating your first item.",
                ),
            ),
            _demo(
                "Chart — bar",
                sc.chart(
                    data=[
                        {"month": "Jan", "sales": 120, "returns": 20},
                        {"month": "Feb", "sales": 180, "returns": 35},
                        {"month": "Mar", "sales": 150, "returns": 28},
                        {"month": "Apr", "sales": 210, "returns": 42},
                        {"month": "May", "sales": 190, "returns": 31},
                        {"month": "Jun", "sales": 240, "returns": 55},
                    ],
                    series=[
                        sc.chart_series("sales", label="Sales"),
                        sc.chart_series("returns", label="Returns"),
                    ],
                    x_key="month",
                    type="bar",
                ),
            ),
        )

    def actions_panel():
        clicks = input.g_btn() if "g_btn" in input else 0
        confirms = input.g_confirm() if "g_confirm" in input else 0

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
                _demo(
                    "Alert dialog",
                    sc.alert_dialog(
                        "g_confirm",
                        trigger_label="Delete item",
                        title="Delete this item?",
                        description="This action cannot be undone.",
                        confirm_label="Delete",
                    ),
                ),
                _demo(
                    "Sheet",
                    sc.sheet(
                        "g_sheet",
                        sc.text_input("g_sheet_name", label="Name"),
                        sc.slider(
                            "g_sheet_lvl", min=0, max=10, value=5, label="Priority"
                        ),
                        trigger_label="Open sheet",
                        title="Edit item",
                        side="right",
                    ),
                ),
            ),
            sc.alert(
                f"button={clicks} clicks · last menu={last_menu()} · "
                f"confirmed={confirms}×",
                title="Live action state",
            ),
        )

    def overlays_panel():
        return _stack(
            _grid(
                _demo(
                    "Drawer",
                    sc.drawer(
                        "g_drawer",
                        sc.badge("Drawer content"),
                        sc.text_input("g_drawer_text", placeholder="Type here…"),
                        trigger_label="Open drawer",
                        title="Drawer",
                        direction="bottom",
                    ),
                ),
                _demo(
                    "Context menu",
                    sc.context_menu(
                        "g_ctx",
                        sc.card(
                            ui.div(
                                "Right-click here",
                                class_="text-sm text-muted-foreground py-4 text-center",
                            ),
                        ),
                        items=[
                            sc.menu_item("copy", "Copy"),
                            sc.menu_item("paste", "Paste"),
                            sc.menu_separator(),
                            sc.menu_item("delete", "Delete", variant="destructive"),
                        ],
                    ),
                ),
            ),
            _demo(
                "Scroll area",
                sc.scroll_area(
                    *[
                        ui.div(
                            sc.badge(f"Item {i}", variant="outline"),
                            class_="py-1",
                        )
                        for i in range(1, 25)
                    ],
                    height="180px",
                ),
            ),
            sc.alert(
                f"Last context menu selection: {last_ctx()}",
                title="Context menu state",
            ),
        )

    def navigation_panel():
        cmd_val = input.g_cmd() if "g_cmd" in input else ""

        return _stack(
            _demo(
                "Menubar",
                sc.menubar(
                    "g_menubar",
                    sc.menubar_menu(
                        "File",
                        sc.menu_item("new", "New"),
                        sc.menu_item("open", "Open"),
                        sc.menu_separator(),
                        sc.menu_item("save", "Save"),
                    ),
                    sc.menubar_menu(
                        "Edit",
                        sc.menu_item("undo", "Undo"),
                        sc.menu_item("redo", "Redo"),
                        sc.menu_separator(),
                        sc.menu_item("cut", "Cut"),
                        sc.menu_item("copy", "Copy"),
                        sc.menu_item("paste", "Paste"),
                    ),
                ),
            ),
            _demo(
                "Navigation menu",
                sc.navigation_menu(
                    sc.nav_item(
                        "Getting Started",
                        items=[
                            sc.nav_item(
                                "Introduction",
                                href="#",
                                description="Re-usable components built with Radix.",
                            ),
                            sc.nav_item(
                                "Installation",
                                href="#",
                                description="How to install and configure.",
                            ),
                        ],
                    ),
                    sc.nav_item(
                        "Components",
                        items=[
                            sc.nav_item("Button", href="#"),
                            sc.nav_item("Card", href="#"),
                            sc.nav_item("Dialog", href="#"),
                        ],
                    ),
                    sc.nav_item("About", href="#"),
                ),
            ),
            _demo(
                "Command palette",
                sc.command(
                    "g_cmd",
                    items=[
                        {
                            "value": "calendar",
                            "label": "Calendar",
                            "group": "Suggestions",
                        },
                        {
                            "value": "emoji",
                            "label": "Search Emoji",
                            "group": "Suggestions",
                        },
                        {
                            "value": "calculator",
                            "label": "Calculator",
                            "group": "Suggestions",
                        },
                        {"value": "profile", "label": "Profile", "group": "Settings"},
                        {"value": "billing", "label": "Billing", "group": "Settings"},
                        {
                            "value": "settings",
                            "label": "Settings",
                            "group": "Settings",
                        },
                    ],
                    placeholder="Search commands…",
                ),
            ),
            sc.alert(
                f"menubar={last_menubar()} · command={cmd_val or '∅'}",
                title="Navigation state",
            ),
        )

    def layout_panel():
        return _stack(
            _demo(
                "Carousel",
                sc.carousel(
                    sc.card(ui.div("Slide 1", class_="p-8 text-center font-semibold")),
                    sc.card(ui.div("Slide 2", class_="p-8 text-center font-semibold")),
                    sc.card(ui.div("Slide 3", class_="p-8 text-center font-semibold")),
                ),
            ),
            _demo(
                "Resizable panels",
                sc.resizable(
                    ui.div(
                        "Panel A",
                        class_="flex items-center justify-center h-full text-sm",
                    ),
                    ui.div(
                        "Panel B",
                        class_="flex items-center justify-center h-full text-sm",
                    ),
                    panels=[{"default_size": 50}, {"default_size": 50}],
                    class_="h-32 rounded-lg border",
                ),
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
                    "shadcn × shinyreact — 47 components, live-wired.",
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
                    sc.tab("overlays", "Overlays"),
                    sc.tab("navigation", "Navigation"),
                    sc.tab("layout", "Layout"),
                    sc.tab("feedback", "Feedback"),
                ],
                inputs_panel(),
                display_panel(),
                actions_panel(),
                overlays_panel(),
                navigation_panel(),
                layout_panel(),
                feedback_panel(),
                selected="inputs",
            ),
            ui.div(
                sc.badge(f"viewing: {active}", variant="secondary"),
                class_="flex",
            ),
        )


app = App(app_ui, server)
