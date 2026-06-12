"""
shadcn × shinyreact — Component Explorer

All 47 components, every variant, fully interactive.
Run: shiny run ui-frameworks/shadcn/examples/shinyreact-shadcn/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py" / "src"))

import shinyreact
import shinyshadcn as sc
from shiny import App, reactive, ui

# ── Page shell ───────────────────────────────────────────────────────────────

# The page-chrome wrapper (outside the React tree) is the ONLY place a string
# `style=` is safe — inside a render_react tree it throws React error #62.
app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("gallery", extra_deps=[sc._dep()]),
        style="max-width: 1120px; margin: 0 auto; padding: 2.5rem 1.25rem;",
    ),
    title="shadcn × shinyreact — Component Explorer",
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _v(label: str, *content: object, wide: bool = False) -> ui.Tag:
    """One variant preview card."""
    extra = " col-span-2" if wide else ""
    return ui.div(
        ui.div(
            label,
            class_=(
                "text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3"
            ),
        ),
        ui.div(*content, class_="flex items-start gap-2 flex-wrap w-full"),
        class_=f"rounded-lg border bg-card p-5 flex flex-col{extra}",
    )


def _sec(name: str, badge: str, subtitle: str, *variants: object) -> ui.Tag:
    """Component section: heading + description + variant grid."""
    return ui.div(
        ui.div(
            ui.div(
                ui.tags.h2(
                    name,
                    class_="text-2xl font-semibold tracking-tight",
                ),
                sc.badge(badge, variant="secondary"),
                class_="flex items-center gap-3",
            ),
            ui.div(subtitle, class_="text-sm text-muted-foreground mt-1"),
            class_="pb-4 border-b mb-6",
        ),
        ui.div(*variants, class_="grid grid-cols-2 gap-4 mb-16"),
    )


# ── Inputs ───────────────────────────────────────────────────────────────────


def _sec_button() -> ui.Tag:
    return _sec(
        "Button",
        "Action",
        "Triggers server events. Six variants, three sizes; click counter via input.",
        _v("Default", sc.button("btn_default", "Click me")),
        _v("Secondary", sc.button("btn_sec", "Secondary", variant="secondary")),
        _v("Destructive", sc.button("btn_del", "Delete", variant="destructive")),
        _v("Outline", sc.button("btn_out", "Outline", variant="outline")),
        _v("Ghost", sc.button("btn_ghost", "Ghost", variant="ghost")),
        _v(
            "Sizes",
            ui.div(
                sc.button("btn_sm", "Small", size="sm"),
                sc.button("btn_md", "Default"),
                sc.button("btn_lg", "Large", size="lg"),
                class_="flex gap-2 items-center flex-wrap",
            ),
        ),
    )


def _sec_text_input() -> ui.Tag:
    return _sec(
        "Text Input",
        "Input",
        "Single-line text field. Reads input.<id>() as a string; debounced by default.",
        _v("Bare", sc.text_input("ti_bare", placeholder="Placeholder text…")),
        _v(
            "With label",
            sc.text_input(
                "ti_label", label="Full name", placeholder="Enter your name…"
            ),
        ),
        _v(
            "No debounce (fires on every keystroke)",
            sc.text_input("ti_fast", placeholder="Immediate…", debounce_ms=0),
        ),
    )


def _sec_textarea() -> ui.Tag:
    return _sec(
        "Textarea",
        "Input",
        "Multi-line text input. Same wire format as text_input.",
        _v("Bare", sc.textarea("ta_bare", placeholder="Write something…")),
        _v(
            "With label",
            sc.textarea("ta_label", label="Notes", placeholder="Add notes here…"),
        ),
    )


def _sec_select() -> ui.Tag:
    return _sec(
        "Select",
        "Input",
        "Dropdown selector. Choices are strings or {value, label} dicts.",
        _v(
            "String list",
            sc.select("sel_str", ["Apple", "Banana", "Cherry", "Durian"]),
        ),
        _v(
            "With label + pre-selected",
            sc.select(
                "sel_lang",
                [
                    {"value": "r", "label": "R"},
                    {"value": "py", "label": "Python"},
                    {"value": "js", "label": "JavaScript"},
                    {"value": "ts", "label": "TypeScript"},
                ],
                label="Language",
                selected="py",
            ),
        ),
    )


def _sec_slider() -> ui.Tag:
    return _sec(
        "Slider",
        "Input",
        "Numeric range slider. Server reads input.<id>() as a number.",
        _v("Default (0–100)", sc.slider("sli_bare", min=0, max=100, value=40)),
        _v(
            "With label",
            sc.slider("sli_label", min=0, max=100, value=65, label="Volume"),
        ),
        _v(
            "Fine steps (0.0–1.0)",
            sc.slider(
                "sli_fine",
                min=0.0,
                max=1.0,
                step=0.05,
                value=0.5,
                label="Opacity",
            ),
        ),
    )


def _sec_checkbox() -> ui.Tag:
    return _sec(
        "Checkbox",
        "Input",
        "Boolean checkbox. Server reads input.<id>() as True/False.",
        _v("Unchecked", sc.checkbox("chk_a", "Accept terms")),
        _v(
            "Checked by default",
            sc.checkbox("chk_b", "Subscribe to updates", checked=True),
        ),
        _v(
            "Multiple",
            ui.div(
                sc.checkbox("chk_c", "Email notifications"),
                sc.checkbox("chk_d", "Weekly digest", checked=True),
                sc.checkbox("chk_e", "Marketing"),
                class_="flex flex-col gap-2",
            ),
        ),
    )


def _sec_switch() -> ui.Tag:
    return _sec(
        "Switch",
        "Input",
        "Toggle switch. Server reads input.<id>() as True/False.",
        _v("Off by default", sc.switch("sw_off", label="Airplane mode")),
        _v("On by default", sc.switch("sw_on", label="Dark mode", checked=True)),
        _v(
            "Multiple",
            ui.div(
                sc.switch("sw_a", label="Wi-Fi", checked=True),
                sc.switch("sw_b", label="Bluetooth"),
                sc.switch("sw_c", label="NFC", checked=True),
                class_="flex flex-col gap-3",
            ),
        ),
    )


def _sec_radio_group() -> ui.Tag:
    return _sec(
        "Radio Group",
        "Input",
        "Single-select from a list. Server reads input.<id>() as the selected string.",
        _v(
            "String choices",
            sc.radio_group(
                "rg_str",
                ["Comfortable", "Compact", "Spacious"],
                selected="Comfortable",
            ),
        ),
        _v(
            "Dict choices + label",
            sc.radio_group(
                "rg_theme",
                [
                    {"value": "light", "label": "Light"},
                    {"value": "dark", "label": "Dark"},
                    {"value": "system", "label": "System"},
                ],
                label="Theme",
                selected="system",
            ),
        ),
    )


def _sec_toggle() -> ui.Tag:
    return _sec(
        "Toggle",
        "Input",
        "Two-state toggle button. Server reads input.<id>() as True/False.",
        _v(
            "Default variant",
            ui.div(
                sc.toggle("tog_a", "Bold"),
                sc.toggle("tog_b", "Italic", pressed=True),
                class_="flex gap-2",
            ),
        ),
        _v(
            "Outline variant",
            ui.div(
                sc.toggle("tog_c", "Outline", variant="outline"),
                sc.toggle("tog_d", "Pressed", variant="outline", pressed=True),
                class_="flex gap-2",
            ),
        ),
        _v(
            "Sizes",
            ui.div(
                sc.toggle("tog_sm", "Sm", size="sm"),
                sc.toggle("tog_md", "Default"),
                sc.toggle("tog_lg", "Lg", size="lg"),
                class_="flex gap-2 items-center",
            ),
        ),
    )


def _sec_toggle_group() -> ui.Tag:
    return _sec(
        "Toggle Group",
        "Input",
        "Set of mutually exclusive (single) or additive (multiple) toggles.",
        _v(
            "Single — text style",
            sc.toggle_group(
                "tgg_fmt",
                ["Bold", "Italic", "Underline"],
                type="single",
                selected="Bold",
            ),
        ),
        _v(
            "Multiple — alignment",
            sc.toggle_group(
                "tgg_align",
                [
                    {"value": "left", "label": "Left"},
                    {"value": "center", "label": "Center"},
                    {"value": "right", "label": "Right"},
                    {"value": "justify", "label": "Justify"},
                ],
                type="multiple",
                selected=["left"],
                variant="outline",
            ),
        ),
    )


def _sec_calendar() -> ui.Tag:
    return _sec(
        "Calendar",
        "Input",
        "Date picker. Server reads input.<id>() as an ISO string (YYYY-MM-DD).",
        _v("Single date", sc.calendar("cal_bare")),
    )


def _sec_input_otp() -> ui.Tag:
    return _sec(
        "Input OTP",
        "Input",
        "Segmented OTP field. Server reads input.<id>() as the entered string.",
        _v("4 slots", sc.input_otp("otp_4", length=4)),
        _v("6 slots with separator", sc.input_otp("otp_6", length=6, separator=True)),
    )


def _sec_pagination() -> ui.Tag:
    return _sec(
        "Pagination",
        "Input",
        "Page-number nav bar. Server reads input.<id>() as a 1-based int.",
        _v(
            "5 pages (no ellipsis)",
            sc.pagination("pg_5", total_pages=5, current=1, show_ellipsis=False),
        ),
        _v(
            "20 pages with ellipsis",
            sc.pagination("pg_20", total_pages=20, current=8),
        ),
    )


# ── Display ──────────────────────────────────────────────────────────────────


def _sec_alert() -> ui.Tag:
    return _sec(
        "Alert",
        "Display",
        "Prominent message box. Display-only — no Shiny input.",
        _v("Default", sc.alert("A neutral informational message.", title="Heads up")),
        _v(
            "Destructive",
            sc.alert(
                "Something went wrong. Please try again.",
                title="Error",
                variant="destructive",
            ),
        ),
        _v("No title", sc.alert("Your changes have been saved successfully.")),
    )


def _sec_badge() -> ui.Tag:
    return _sec(
        "Badge",
        "Display",
        "Small inline label. Four visual variants.",
        _v(
            "All variants",
            ui.div(
                sc.badge("Default"),
                sc.badge("Secondary", variant="secondary"),
                sc.badge("Destructive", variant="destructive"),
                sc.badge("Outline", variant="outline"),
                class_="flex gap-2 flex-wrap",
            ),
        ),
    )


def _sec_avatar() -> ui.Tag:
    return _sec(
        "Avatar",
        "Display",
        "User avatar with initials fallback. Three sizes.",
        _v(
            "Sizes",
            ui.div(
                sc.avatar(fallback="SM", size="sm"),
                sc.avatar(fallback="MD"),
                sc.avatar(fallback="LG", size="lg"),
                class_="flex gap-3 items-center",
            ),
        ),
        _v(
            "Multiple initials",
            ui.div(
                sc.avatar(fallback="AB"),
                sc.avatar(fallback="JD"),
                sc.avatar(fallback="KL"),
                sc.avatar(fallback="MN"),
                sc.avatar(fallback="ZR"),
                class_="flex gap-2",
            ),
        ),
    )


def _sec_card() -> ui.Tag:
    return _sec(
        "Card",
        "Container",
        "Bordered content container with an optional title header.",
        _v(
            "With title",
            sc.card(
                ui.div(
                    "Card body content goes here.",
                    class_="text-sm text-muted-foreground",
                ),
                title="Card title",
            ),
        ),
        _v(
            "No header",
            sc.card(ui.div("Just a content card, no title.", class_="text-sm")),
        ),
        _v(
            "Rich content",
            sc.card(
                ui.div(
                    sc.badge("New", variant="secondary"),
                    ui.tags.h3("Feature update", class_="font-semibold mt-2"),
                    ui.div(
                        "Version 2.0 is now available.",
                        class_="text-sm text-muted-foreground mt-1",
                    ),
                ),
                title="Announcement",
            ),
        ),
    )


def _sec_table() -> ui.Tag:
    return _sec(
        "Table",
        "Display",
        "Data table. Columns and rows as Python lists.",
        _v(
            "Sample data",
            sc.table(
                columns=["Name", "Status", "Revenue"],
                rows=[
                    ["Acme Corp", "Active", "$12,400"],
                    ["Globex", "Inactive", "$3,200"],
                    ["Initech", "Active", "$8,750"],
                    ["Umbrella", "Pending", "$5,100"],
                    ["Aperture", "Active", "$21,050"],
                ],
                caption="Q4 accounts",
            ),
            wide=True,
        ),
    )


def _sec_skeleton() -> ui.Tag:
    return _sec(
        "Skeleton",
        "Display",
        "Loading placeholder. Shape and size it with class_.",
        _v(
            "Text block",
            ui.div(
                sc.skeleton(class_="h-4 w-full"),
                sc.skeleton(class_="h-4 w-5/6"),
                sc.skeleton(class_="h-4 w-3/4"),
                sc.skeleton(class_="h-4 w-1/2"),
                class_="flex flex-col gap-2 w-full",
            ),
        ),
        _v(
            "Card",
            ui.div(
                sc.skeleton(class_="h-32 w-full rounded-lg"),
                sc.skeleton(class_="h-4 w-3/4 mt-3"),
                sc.skeleton(class_="h-4 w-1/2 mt-2"),
                class_="w-full",
            ),
        ),
        _v(
            "Avatar + text",
            ui.div(
                sc.skeleton(class_="size-10 rounded-full shrink-0"),
                ui.div(
                    sc.skeleton(class_="h-4 w-28"),
                    sc.skeleton(class_="h-3 w-20 mt-1"),
                    class_="flex flex-col gap-1 flex-1",
                ),
                class_="flex items-center gap-3 w-full",
            ),
        ),
    )


def _sec_spinner() -> ui.Tag:
    return _sec(
        "Spinner",
        "Display",
        "Animated loading indicator. Size via class_ (e.g. size-6).",
        _v(
            "Sizes",
            ui.div(
                sc.spinner(class_="size-4"),
                sc.spinner(class_="size-6"),
                sc.spinner(class_="size-8"),
                sc.spinner(class_="size-12"),
                class_="flex gap-5 items-center",
            ),
        ),
    )


def _sec_progress() -> ui.Tag:
    return _sec(
        "Progress",
        "Display",
        "Determinate progress bar. Value 0–100.",
        _v("0%", ui.div(sc.progress(0), class_="w-full")),
        _v("33%", ui.div(sc.progress(33), class_="w-full")),
        _v("66%", ui.div(sc.progress(66), class_="w-full")),
        _v("100%", ui.div(sc.progress(100), class_="w-full")),
    )


def _sec_chart() -> ui.Tag:
    _data = [
        {"month": "Jan", "sales": 120, "returns": 20},
        {"month": "Feb", "sales": 180, "returns": 35},
        {"month": "Mar", "sales": 150, "returns": 28},
        {"month": "Apr", "sales": 210, "returns": 42},
        {"month": "May", "sales": 190, "returns": 31},
        {"month": "Jun", "sales": 240, "returns": 55},
    ]
    _series = [
        sc.chart_series("sales", label="Sales"),
        sc.chart_series("returns", label="Returns"),
    ]
    return _sec(
        "Chart",
        "Display",
        "Recharts wrapper. Four types: bar, line, area, pie.",
        _v(
            "Bar",
            sc.chart(_data, _series, type="bar", x_key="month", height=220),
            wide=True,
        ),
        _v(
            "Line",
            sc.chart(_data, _series, type="line", x_key="month", height=220),
            wide=True,
        ),
        _v(
            "Area",
            sc.chart(_data, _series, type="area", x_key="month", height=220),
            wide=True,
        ),
    )


def _sec_separator() -> ui.Tag:
    return _sec(
        "Separator",
        "Display",
        "Thin rule for visual separation. Horizontal or vertical.",
        _v(
            "Horizontal",
            ui.div(
                ui.div("Section above", class_="text-sm"),
                sc.separator(),
                ui.div("Section below", class_="text-sm"),
                class_="flex flex-col gap-3 w-full",
            ),
        ),
        _v(
            "Vertical (in a flex row)",
            ui.div(
                ui.div("Left", class_="text-sm px-3"),
                sc.separator(orientation="vertical", class_="h-5"),
                ui.div("Center", class_="text-sm px-3"),
                sc.separator(orientation="vertical", class_="h-5"),
                ui.div("Right", class_="text-sm px-3"),
                class_="flex items-center",
            ),
        ),
    )


def _sec_label() -> ui.Tag:
    return _sec(
        "Label",
        "Display",
        "Semantic text label, typically paired with form inputs.",
        _v("Standalone", sc.label("Email address")),
        _v(
            "Stacked list",
            ui.div(
                sc.label("First name"),
                sc.separator(),
                sc.label("Last name"),
                sc.separator(),
                sc.label("Company"),
                class_="flex flex-col gap-2 w-full",
            ),
        ),
    )


def _sec_kbd() -> ui.Tag:
    return _sec(
        "Kbd",
        "Display",
        "Keyboard key hint.",
        _v(
            "Single keys",
            ui.div(
                sc.kbd("⌘"),
                sc.kbd("⇧"),
                sc.kbd("⌥"),
                sc.kbd("⌫"),
                sc.kbd("⏎"),
                sc.kbd("Esc"),
                class_="flex gap-2 flex-wrap",
            ),
        ),
        _v(
            "Combos",
            ui.div(
                ui.div(
                    sc.kbd("⌘"),
                    ui.div("+", class_="text-xs text-muted-foreground"),
                    sc.kbd("K"),
                    class_="flex gap-1 items-center",
                ),
                ui.div(
                    sc.kbd("⌘"),
                    ui.div("+", class_="text-xs text-muted-foreground"),
                    sc.kbd("⇧"),
                    ui.div("+", class_="text-xs text-muted-foreground"),
                    sc.kbd("P"),
                    class_="flex gap-1 items-center",
                ),
                class_="flex gap-6",
            ),
        ),
        _v(
            "In context",
            ui.div(
                ui.div(
                    ui.div("Save", class_="text-sm"),
                    ui.div(sc.kbd("⌘"), sc.kbd("S"), class_="flex gap-1"),
                    class_="flex justify-between items-center",
                ),
                ui.div(
                    ui.div("Open palette", class_="text-sm"),
                    ui.div(sc.kbd("⌘"), sc.kbd("K"), class_="flex gap-1"),
                    class_="flex justify-between items-center",
                ),
                ui.div(
                    ui.div("Format", class_="text-sm"),
                    ui.div(
                        sc.kbd("⌘"),
                        sc.kbd("⇧"),
                        sc.kbd("F"),
                        class_="flex gap-1",
                    ),
                    class_="flex justify-between items-center",
                ),
                class_="flex flex-col gap-2 w-full",
            ),
        ),
    )


def _sec_empty() -> ui.Tag:
    return _sec(
        "Empty",
        "Display",
        "Empty-state panel. Children become the action area.",
        _v(
            "With action",
            sc.empty(
                sc.button("empty_btn_a", "Create item"),
                title="No items yet",
                description="Get started by creating your first item.",
            ),
        ),
        _v(
            "Description only",
            sc.empty(
                title="No results found",
                description="Try adjusting your search or filter.",
            ),
        ),
    )


# ── Overlays ─────────────────────────────────────────────────────────────────


def _sec_dialog() -> ui.Tag:
    return _sec(
        "Dialog",
        "Overlay",
        "Modal panel. Server reads input.<id>() as bool (open state).",
        _v(
            "Basic",
            sc.dialog(
                "dlg_basic",
                ui.div("Dialog body content goes here.", class_="text-sm"),
                trigger_label="Open dialog",
                title="Dialog title",
                description="Supporting description text.",
            ),
        ),
        _v(
            "With form inputs",
            sc.dialog(
                "dlg_form",
                sc.text_input("dlg_name", label="Name", placeholder="Your name…"),
                sc.slider("dlg_age", min=18, max=99, value=30, label="Age"),
                sc.select(
                    "dlg_role",
                    ["Engineer", "Designer", "Manager", "Other"],
                    label="Role",
                ),
                trigger_label="Edit profile",
                title="Edit profile",
                description="Update your account information.",
            ),
        ),
    )


def _sec_alert_dialog() -> ui.Tag:
    return _sec(
        "Alert Dialog",
        "Overlay",
        "Blocking confirmation. confirm_id increments on confirm.",
        _v(
            "Destructive confirm",
            sc.alert_dialog(
                "adlg_del",
                trigger_label="Delete account",
                title="Delete your account?",
                description=(
                    "This action cannot be undone."
                    " All your data will be permanently removed."
                ),
                confirm_label="Yes, delete",
            ),
        ),
        _v(
            "Neutral confirm",
            sc.alert_dialog(
                "adlg_confirm",
                trigger_label="Publish post",
                title="Publish this post?",
                description="The post will be visible to all users immediately.",
                confirm_label="Publish",
            ),
        ),
    )


def _sec_drawer() -> ui.Tag:
    return _sec(
        "Drawer",
        "Overlay",
        "Edge-anchored swipe panel (vaul). Server reads open state as bool.",
        _v(
            "From bottom",
            sc.drawer(
                "drw_bot",
                sc.text_input("drw_search", placeholder="Search…"),
                sc.badge("Drawer content area", variant="outline"),
                trigger_label="Open bottom drawer",
                title="Bottom drawer",
                direction="bottom",
            ),
        ),
        _v(
            "From right",
            sc.drawer(
                "drw_right",
                sc.badge("Right-side content", variant="secondary"),
                sc.text_input("drw_note", label="Note", placeholder="Add a note…"),
                trigger_label="Open right drawer",
                title="Right drawer",
                direction="right",
            ),
        ),
    )


def _sec_sheet() -> ui.Tag:
    return _sec(
        "Sheet",
        "Overlay",
        "Side panel. Slides in from an edge. Server reads open state as bool.",
        _v(
            "From right",
            sc.sheet(
                "sht_right",
                sc.text_input("sht_name", label="Name"),
                sc.slider("sht_lvl", min=0, max=10, value=5, label="Priority"),
                sc.textarea("sht_notes", label="Notes", placeholder="Add notes…"),
                trigger_label="Open right sheet",
                title="Edit item",
                side="right",
            ),
        ),
        _v(
            "From left",
            sc.sheet(
                "sht_left",
                sc.badge("Navigation panel", variant="outline"),
                sc.separator(),
                ui.div("Menu item 1", class_="text-sm py-2"),
                ui.div("Menu item 2", class_="text-sm py-2"),
                ui.div("Menu item 3", class_="text-sm py-2"),
                trigger_label="Open left sheet",
                title="Navigation",
                side="left",
            ),
        ),
    )


def _sec_popover() -> ui.Tag:
    return _sec(
        "Popover",
        "Overlay",
        "Small floating panel anchored to a trigger button.",
        _v(
            "Default",
            sc.popover(
                "pop_basic",
                sc.badge("Inside the popover"),
                sc.text_input("pop_input", placeholder="Type here…"),
                trigger_label="Open popover",
            ),
        ),
        _v(
            "Align start",
            sc.popover(
                "pop_start",
                ui.div("Anchored to the start edge.", class_="text-sm"),
                sc.separator(),
                sc.slider("pop_sli", min=0, max=100, value=50, label="Setting"),
                trigger_label="Anchored popover",
                align="start",
            ),
        ),
    )


def _sec_dropdown_menu() -> ui.Tag:
    return _sec(
        "Dropdown Menu",
        "Overlay",
        "Contextual action menu. input.<id>() fires {value, nonce} on click.",
        _v(
            "With groups + separator",
            sc.dropdown_menu(
                "ddm_basic",
                sc.menu_label("Actions"),
                sc.menu_item("edit", "Edit"),
                sc.menu_item("duplicate", "Duplicate"),
                sc.menu_separator(),
                sc.menu_item("delete", "Delete", variant="destructive"),
                trigger_label="Open menu",
            ),
        ),
        _v(
            "With submenu + checkbox",
            sc.dropdown_menu(
                "ddm_sub",
                sc.menu_item("new", "New file"),
                sc.menu_item("open", "Open file…"),
                sc.menu_submenu(
                    "Move to",
                    sc.menu_item("inbox", "Inbox"),
                    sc.menu_item("archive", "Archive"),
                    sc.menu_item("trash", "Trash"),
                ),
                sc.menu_separator(),
                sc.menu_checkbox("ddm_chk", "Show hidden files"),
                trigger_label="File menu",
            ),
        ),
    )


def _sec_context_menu() -> ui.Tag:
    return _sec(
        "Context Menu",
        "Overlay",
        "Right-click menu. Children define the trigger area.",
        _v(
            "Right-click zone",
            sc.context_menu(
                "ctx_basic",
                sc.card(
                    ui.div(
                        "Right-click anywhere in this card",
                        class_=(
                            "text-sm text-muted-foreground py-8 text-center select-none"
                        ),
                    ),
                    class_="w-full",
                ),
                items=[
                    sc.menu_item("copy", "Copy"),
                    sc.menu_item("paste", "Paste"),
                    sc.menu_item("select_all", "Select all"),
                    sc.menu_separator(),
                    sc.menu_item("delete", "Delete", variant="destructive"),
                ],
            ),
            wide=True,
        ),
    )


def _sec_tooltip() -> ui.Tag:
    return _sec(
        "Tooltip",
        "Overlay",
        "Hover tooltip. Children = trigger element, content = tooltip text.",
        _v(
            "Four sides",
            ui.div(
                sc.tooltip(sc.badge("Top"), content="Tooltip on top", side="top"),
                sc.tooltip(sc.badge("Right"), content="Tooltip on right", side="right"),
                sc.tooltip(
                    sc.badge("Bottom"), content="Tooltip on bottom", side="bottom"
                ),
                sc.tooltip(sc.badge("Left"), content="Tooltip on left", side="left"),
                class_="flex gap-3 flex-wrap",
            ),
        ),
        _v(
            "On a button",
            sc.tooltip(
                sc.button("tip_btn", "Hover for help"),
                content="Submits the form and saves your changes",
                side="top",
            ),
        ),
    )


def _sec_hover_card() -> ui.Tag:
    return _sec(
        "Hover Card",
        "Overlay",
        "Rich card revealed on hover over a trigger link.",
        _v(
            "User profile card",
            sc.hover_card(
                sc.card(
                    ui.div(
                        ui.div(
                            sc.avatar(fallback="SC"),
                            ui.div(
                                ui.div("@shadcn", class_="font-semibold text-sm"),
                                ui.div(
                                    "Component library author",
                                    class_="text-xs text-muted-foreground",
                                ),
                                class_="flex flex-col",
                            ),
                            class_="flex items-center gap-3",
                        ),
                        ui.div(
                            "Building beautiful component libraries for React.",
                            class_="text-sm text-muted-foreground mt-2",
                        ),
                        ui.div(
                            sc.badge("42 followers", variant="outline"),
                            sc.badge("128 following", variant="outline"),
                            class_="flex gap-2 mt-3",
                        ),
                    ),
                ),
                trigger_label="@shadcn",
            ),
        ),
    )


# ── Navigation ───────────────────────────────────────────────────────────────


def _sec_breadcrumb() -> ui.Tag:
    return _sec(
        "Breadcrumb",
        "Navigation",
        "Trail of navigation links. The last item is the current page.",
        _v(
            "3-level",
            sc.breadcrumb(
                sc.crumb("Home", href="#"),
                sc.crumb("Settings", href="#"),
                sc.crumb("Profile"),
            ),
        ),
        _v(
            "Deeper path",
            sc.breadcrumb(
                sc.crumb("Home", href="#"),
                sc.crumb("Library", href="#"),
                sc.crumb("Components", href="#"),
                sc.crumb("Button"),
            ),
        ),
    )


def _sec_tabs() -> ui.Tag:
    return _sec(
        "Tabs",
        "Navigation",
        "Tabbed panel. Active tab tracked as input.<id>().",
        _v(
            "3 tabs",
            sc.tabs(
                "tab_demo",
                [
                    sc.tab("account", "Account"),
                    sc.tab("password", "Password"),
                    sc.tab("billing", "Billing"),
                ],
                ui.div(
                    "Manage your account settings here.",
                    class_="text-sm text-muted-foreground py-2",
                ),
                ui.div(
                    "Change your password and security settings.",
                    class_="text-sm text-muted-foreground py-2",
                ),
                ui.div(
                    "View invoices and manage your plan.",
                    class_="text-sm text-muted-foreground py-2",
                ),
                selected="account",
            ),
            wide=True,
        ),
    )


def _sec_accordion() -> ui.Tag:
    return _sec(
        "Accordion",
        "Navigation",
        "Expandable sections. Single or multiple items open at once.",
        _v(
            "Single open",
            sc.accordion(
                "acc_single",
                [
                    sc.accordion_item("q1", "Is it accessible?"),
                    sc.accordion_item("q2", "Is it styled?"),
                    sc.accordion_item("q3", "Is it animated?"),
                ],
                ui.div(
                    "Yes. Adheres to the WAI-ARIA design pattern.",
                    class_="text-sm",
                ),
                ui.div(
                    "Yes. Comes with default styles that match the design.",
                    class_="text-sm",
                ),
                ui.div(
                    "Yes. Animation handled by CSS transitions.",
                    class_="text-sm",
                ),
                type="single",
                selected="q1",
            ),
        ),
        _v(
            "Multiple open",
            sc.accordion(
                "acc_multi",
                [
                    sc.accordion_item("m1", "Section A"),
                    sc.accordion_item("m2", "Section B"),
                    sc.accordion_item("m3", "Section C"),
                ],
                ui.div("Content for section A.", class_="text-sm"),
                ui.div("Content for section B.", class_="text-sm"),
                ui.div("Content for section C.", class_="text-sm"),
                type="multiple",
                selected=["m1", "m3"],
            ),
        ),
    )


def _sec_navigation_menu() -> ui.Tag:
    return _sec(
        "Navigation Menu",
        "Navigation",
        "Horizontal nav bar with optional dropdown sub-menus.",
        _v(
            "With dropdowns",
            sc.navigation_menu(
                sc.nav_item(
                    "Docs",
                    items=[
                        sc.nav_item(
                            "Introduction",
                            href="#",
                            description="Get started with shinyreact.",
                        ),
                        sc.nav_item(
                            "Installation",
                            href="#",
                            description="How to install and configure.",
                        ),
                        sc.nav_item(
                            "Components",
                            href="#",
                            description="Full component reference.",
                        ),
                    ],
                ),
                sc.nav_item("API", href="#"),
                sc.nav_item("GitHub", href="#"),
            ),
            wide=True,
        ),
    )


def _sec_menubar() -> ui.Tag:
    return _sec(
        "Menubar",
        "Navigation",
        "Horizontal menu bar with multiple dropdowns. Fires input.<id>() on click.",
        _v(
            "File / Edit / View",
            sc.menubar(
                "mb_demo",
                sc.menubar_menu(
                    "File",
                    sc.menu_item("new", "New"),
                    sc.menu_item("open", "Open…"),
                    sc.menu_separator(),
                    sc.menu_item("save", "Save"),
                    sc.menu_item("saveas", "Save as…"),
                    sc.menu_separator(),
                    sc.menu_item("quit", "Quit"),
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
                sc.menubar_menu(
                    "View",
                    sc.menu_item("zoom_in", "Zoom In"),
                    sc.menu_item("zoom_out", "Zoom Out"),
                    sc.menu_item("reset_zoom", "Reset Zoom"),
                    sc.menu_separator(),
                    sc.menu_checkbox("mb_sidebar", "Show Sidebar", checked=True),
                    sc.menu_checkbox("mb_statusbar", "Show Status Bar"),
                ),
            ),
            wide=True,
        ),
    )


def _sec_command() -> ui.Tag:
    return _sec(
        "Command",
        "Navigation",
        "Searchable command palette. Server reads input.<id>() as the selected value.",
        _v(
            "With groups + search",
            sc.command(
                "cmd_demo",
                items=[
                    {"value": "calendar", "label": "Calendar", "group": "Suggestions"},
                    {"value": "emoji", "label": "Search Emoji", "group": "Suggestions"},
                    {
                        "value": "calculator",
                        "label": "Calculator",
                        "group": "Suggestions",
                    },
                    {"value": "profile", "label": "Profile", "group": "Settings"},
                    {"value": "billing", "label": "Billing", "group": "Settings"},
                    {"value": "settings", "label": "Settings", "group": "Settings"},
                    {"value": "logout", "label": "Log out", "group": "Settings"},
                ],
                placeholder="Type a command or search…",
            ),
            wide=True,
        ),
    )


def _sec_collapsible() -> ui.Tag:
    return _sec(
        "Collapsible",
        "Navigation",
        "Disclosure widget. Server reads input.<id>() as bool (open).",
        _v(
            "Default closed",
            sc.collapsible(
                "col_a",
                ui.div(
                    "Hidden content revealed when you click the trigger.",
                    class_="text-sm text-muted-foreground",
                ),
                trigger_label="Show details",
            ),
        ),
        _v(
            "Default open",
            sc.collapsible(
                "col_b",
                ui.div(
                    "This content is visible by default.",
                    class_="text-sm text-muted-foreground",
                ),
                trigger_label="Hide details",
                open=True,
            ),
        ),
    )


# ── Layout ───────────────────────────────────────────────────────────────────


def _sec_carousel() -> ui.Tag:
    return _sec(
        "Carousel",
        "Layout",
        "Slide carousel (embla). Each child becomes one slide.",
        _v(
            "Horizontal (4 slides)",
            sc.carousel(
                sc.card(
                    ui.div(
                        "Slide 1",
                        class_="p-10 text-center font-semibold text-lg",
                    )
                ),
                sc.card(
                    ui.div(
                        "Slide 2",
                        class_="p-10 text-center font-semibold text-lg",
                    )
                ),
                sc.card(
                    ui.div(
                        "Slide 3",
                        class_="p-10 text-center font-semibold text-lg",
                    )
                ),
                sc.card(
                    ui.div(
                        "Slide 4",
                        class_="p-10 text-center font-semibold text-lg",
                    )
                ),
            ),
            wide=True,
        ),
        _v(
            "Loop enabled",
            sc.carousel(
                sc.card(ui.div("A", class_="p-10 text-center font-bold text-2xl")),
                sc.card(ui.div("B", class_="p-10 text-center font-bold text-2xl")),
                sc.card(ui.div("C", class_="p-10 text-center font-bold text-2xl")),
                loop=True,
            ),
        ),
    )


def _sec_resizable() -> ui.Tag:
    return _sec(
        "Resizable",
        "Layout",
        "Panels separated by draggable handles.",
        _v(
            "2 panels — horizontal",
            ui.div(
                sc.resizable(
                    ui.div(
                        "Panel A",
                        class_=(
                            "flex items-center justify-center"
                            " h-full text-sm font-medium"
                        ),
                    ),
                    ui.div(
                        "Panel B",
                        class_=(
                            "flex items-center justify-center"
                            " h-full text-sm font-medium"
                        ),
                    ),
                    panels=[{"default_size": 50}, {"default_size": 50}],
                    class_="h-24 rounded-lg border",
                ),
                class_="w-full",
            ),
        ),
        _v(
            "3 panels",
            ui.div(
                sc.resizable(
                    ui.div(
                        "A",
                        class_=(
                            "flex items-center justify-center"
                            " h-full text-sm font-medium"
                        ),
                    ),
                    ui.div(
                        "B",
                        class_=(
                            "flex items-center justify-center"
                            " h-full text-sm font-medium"
                        ),
                    ),
                    ui.div(
                        "C",
                        class_=(
                            "flex items-center justify-center"
                            " h-full text-sm font-medium"
                        ),
                    ),
                    panels=[
                        {"default_size": 33},
                        {"default_size": 34},
                        {"default_size": 33},
                    ],
                    class_="h-24 rounded-lg border",
                ),
                class_="w-full",
            ),
        ),
        _v(
            "Vertical split",
            ui.div(
                sc.resizable(
                    ui.div(
                        "Top",
                        class_=(
                            "flex items-center justify-center"
                            " h-full text-sm font-medium"
                        ),
                    ),
                    ui.div(
                        "Bottom",
                        class_=(
                            "flex items-center justify-center"
                            " h-full text-sm font-medium"
                        ),
                    ),
                    orientation="vertical",
                    panels=[{"default_size": 50}, {"default_size": 50}],
                    class_="h-36 rounded-lg border",
                ),
                class_="w-full",
            ),
        ),
    )


def _sec_scroll_area() -> ui.Tag:
    return _sec(
        "Scroll Area",
        "Layout",
        "Scrollable container with styled scrollbar.",
        _v(
            "Vertical list",
            sc.scroll_area(
                *[
                    ui.div(
                        sc.badge(f"Item {i:02d}", variant="outline"),
                        class_="py-1",
                    )
                    for i in range(1, 35)
                ],
                height="200px",
            ),
        ),
        _v(
            "Horizontal tags",
            ui.div(
                sc.scroll_area(
                    ui.div(
                        *[
                            sc.badge(f"Tag {i}", variant="secondary")
                            for i in range(1, 24)
                        ],
                        class_="flex gap-2 w-max px-1",
                    ),
                    orientation="horizontal",
                    height="40px",
                ),
                class_="w-full",
            ),
        ),
    )


def _sec_aspect_ratio() -> ui.Tag:
    return _sec(
        "Aspect Ratio",
        "Layout",
        "Fixed-ratio container. Children fill the box.",
        _v(
            "16:9 — video",
            sc.aspect_ratio(
                ui.div(
                    ui.div(
                        "16 : 9", class_="text-sm font-medium text-muted-foreground"
                    ),
                    class_=(
                        "flex items-center justify-center h-full rounded-lg bg-muted"
                    ),
                ),
                ratio=16 / 9,
            ),
        ),
        _v(
            "1:1 — square",
            sc.aspect_ratio(
                ui.div(
                    ui.div("1 : 1", class_="text-sm font-medium text-muted-foreground"),
                    class_=(
                        "flex items-center justify-center h-full rounded-lg bg-muted"
                    ),
                ),
                ratio=1.0,
            ),
        ),
        _v(
            "4:3 — classic",
            sc.aspect_ratio(
                ui.div(
                    ui.div("4 : 3", class_="text-sm font-medium text-muted-foreground"),
                    class_=(
                        "flex items-center justify-center h-full rounded-lg bg-muted"
                    ),
                ),
                ratio=4 / 3,
            ),
        ),
    )


# ── Feedback ─────────────────────────────────────────────────────────────────


def _sec_toaster() -> ui.Tag:
    return _sec(
        "Toast (Sonner)",
        "Feedback",
        "Server-push notifications. Mount toaster() once; call sc.toast() server-side.",
        _v("Default", sc.button("toast_default", "Show toast")),
        _v("Success", sc.button("toast_success", "Success", variant="outline")),
        _v("Error", sc.button("toast_error", "Error", variant="outline")),
        _v("Info", sc.button("toast_info", "Info", variant="outline")),
        _v("Warning", sc.button("toast_warning", "Warning", variant="outline")),
    )


# ── Section registry ─────────────────────────────────────────────────────────

_SECTIONS: dict[str, list] = {
    "inputs": [
        _sec_button,
        _sec_text_input,
        _sec_textarea,
        _sec_select,
        _sec_slider,
        _sec_checkbox,
        _sec_switch,
        _sec_radio_group,
        _sec_toggle,
        _sec_toggle_group,
        _sec_calendar,
        _sec_input_otp,
        _sec_pagination,
    ],
    "display": [
        _sec_alert,
        _sec_badge,
        _sec_avatar,
        _sec_card,
        _sec_table,
        _sec_skeleton,
        _sec_spinner,
        _sec_progress,
        _sec_chart,
        _sec_separator,
        _sec_label,
        _sec_kbd,
        _sec_empty,
    ],
    "overlays": [
        _sec_dialog,
        _sec_alert_dialog,
        _sec_drawer,
        _sec_sheet,
        _sec_popover,
        _sec_dropdown_menu,
        _sec_context_menu,
        _sec_tooltip,
        _sec_hover_card,
    ],
    "nav": [
        _sec_breadcrumb,
        _sec_tabs,
        _sec_accordion,
        _sec_navigation_menu,
        _sec_menubar,
        _sec_command,
        _sec_collapsible,
    ],
    "layout": [
        _sec_carousel,
        _sec_resizable,
        _sec_scroll_area,
        _sec_aspect_ratio,
    ],
    "feedback": [_sec_toaster],
}

_CAT_CHOICES = [
    {"value": "inputs", "label": "Inputs · 13"},
    {"value": "display", "label": "Display · 13"},
    {"value": "overlays", "label": "Overlays · 9"},
    {"value": "nav", "label": "Navigation · 7"},
    {"value": "layout", "label": "Layout · 4"},
    {"value": "feedback", "label": "Feedback · 1"},
]

# ── Server ────────────────────────────────────────────────────────────────────


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.toast_default, ignore_init=True)
    async def _toast_default():
        await sc.toast(session, "Event fired!", description="Button was clicked.")

    @reactive.effect
    @reactive.event(input.toast_success, ignore_init=True)
    async def _toast_success():
        await sc.toast(
            session, "Saved!", description="Your changes were saved.", type="success"
        )

    @reactive.effect
    @reactive.event(input.toast_error, ignore_init=True)
    async def _toast_error():
        await sc.toast(
            session,
            "Something went wrong",
            description="Please try again later.",
            type="error",
        )

    @reactive.effect
    @reactive.event(input.toast_info, ignore_init=True)
    async def _toast_info():
        await sc.toast(
            session,
            "Did you know?",
            description="You can stack multiple toasts at once.",
            type="info",
        )

    @reactive.effect
    @reactive.event(input.toast_warning, ignore_init=True)
    async def _toast_warning():
        await sc.toast(
            session,
            "Heads up",
            description="This action may have side effects.",
            type="warning",
        )

    @shinyreact.render_react
    def gallery():
        cat = input.cat() if "cat" in input else "inputs"
        fns = _SECTIONS.get(cat, _SECTIONS["inputs"])

        return ui.div(
            sc.toaster(position="bottom-right"),
            # ── Hero ──────────────────────────────────────────────────────
            ui.div(
                ui.tags.h1(
                    "shadcn × shinyreact",
                    class_="text-3xl font-bold tracking-tight",
                ),
                ui.div(
                    "47 components · every variant · fully interactive",
                    class_="text-muted-foreground mt-2 text-base",
                ),
                class_="flex flex-col pb-6 border-b mb-8",
            ),
            # ── Category nav ──────────────────────────────────────────────
            ui.div(
                sc.toggle_group(
                    "cat",
                    _CAT_CHOICES,
                    type="single",
                    selected=cat,
                    variant="outline",
                    class_="flex-wrap",
                ),
                class_="mb-10",
            ),
            # ── Content ───────────────────────────────────────────────────
            ui.div(*[fn() for fn in fns], class_="flex flex-col"),
        )


app = App(app_ui, server)
