"""Component gallery — every shinymui component and its variants in one showcase.

Layout and spacing come entirely from MUI's own components (Container, Stack with
`spacing`, Card, Divider) since MUI has no Tailwind. Run:
    shiny run ui-frameworks/mui/examples/gallery-py/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py" / "src"))

import shinymui as mui
import shinyreact
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("gallery", extra_deps=[mui._dep()]),
        style="margin: 2rem auto; max-width: 1040px; padding: 0 1rem;",
    ),
    title="shinymui gallery",
)


def demo(label: str, *nodes: object) -> object:
    """One labeled component demo: an overline caption above the component(s)."""
    return mui.stack(
        mui.typography(label, variant="overline", color="text.secondary"),
        *nodes,
        spacing=1.5,
    )


def row(*nodes: object) -> object:
    """Variants laid out horizontally with spacing."""
    return mui.stack(*nodes, direction="row", spacing=2)


def section(title: str, *demos: object) -> object:
    """A titled section: heading + a Card whose body stacks the demos."""
    return mui.stack(
        mui.typography(title, variant="h5"),
        mui.card(mui.stack(*demos, spacing=3)),
        spacing=2,
    )


def inputs_section() -> object:
    return section(
        "Inputs",
        demo(
            "button — variants & colors",
            row(
                mui.button("g_btn_contained", "Contained"),
                mui.button("g_btn_outlined", "Outlined", variant="outlined"),
                mui.button("g_btn_text", "Text", variant="text"),
                mui.button("g_btn_error", "Error", color="error"),
            ),
        ),
        demo(
            "fab",
            row(
                mui.fab("g_fab1", "+"),
                mui.fab("g_fab2", "Go", color="secondary", variant="extended"),
            ),
        ),
        demo(
            "text_field — variants",
            mui.text_field("g_tf_outlined", label="Outlined"),
            mui.text_field("g_tf_filled", label="Filled", variant="filled"),
            mui.text_field("g_tf_standard", label="Standard", variant="standard"),
        ),
        demo("slider", mui.slider("g_slider", value=30)),
        demo("rating", mui.rating("g_rating", max=5)),
        demo(
            "switch / checkbox",
            row(
                mui.switch("g_switch", label="Switch"),
                mui.checkbox("g_checkbox", label="Checkbox"),
            ),
        ),
        demo(
            "radio_group",
            mui.radio_group("g_radio", ["One", "Two", "Three"], label="Pick one"),
        ),
        demo("select", mui.select("g_select", ["Red", "Green", "Blue"], label="Color")),
        demo(
            "autocomplete",
            mui.autocomplete(
                "g_auto", ["Apple", "Banana", "Cherry", "Date"], label="Fruit"
            ),
        ),
        demo(
            "toggle_button_group",
            mui.toggle_button_group("g_tbg", ["left", "center", "right"]),
        ),
        demo("pagination", mui.pagination("g_pag", count=10)),
        demo(
            "bottom_navigation",
            mui.bottom_navigation(
                "g_bn",
                [
                    {"value": "home", "label": "Home"},
                    {"value": "favorites", "label": "Favorites"},
                    {"value": "profile", "label": "Profile"},
                ],
            ),
        ),
        demo(
            "tabs",
            mui.tabs(
                "g_tabs",
                [{"value": "a", "label": "Tab A"}, {"value": "b", "label": "Tab B"}],
                mui.typography("Panel A content."),
                mui.typography("Panel B content."),
            ),
        ),
    )


def display_section() -> object:
    return section(
        "Display",
        demo(
            "typography — variants",
            mui.typography("h6 heading", variant="h6"),
            mui.typography("Body text — the quick brown fox.", variant="body1"),
            mui.typography("Caption text", variant="caption"),
        ),
        demo(
            "alert — severities",
            mui.alert("Success message", severity="success"),
            mui.alert("Info message", severity="info"),
            mui.alert("Warning message", severity="warning"),
            mui.alert("Error message", severity="error"),
        ),
        demo(
            "avatar",
            row(mui.avatar(text="AB"), mui.avatar(text="CD"), mui.avatar(text="EF")),
        ),
        demo("badge", mui.badge(mui.typography("Inbox"), badge_content=4)),
        demo(
            "chip — variants",
            row(
                mui.chip("Default"),
                mui.chip("Primary", color="primary"),
                mui.chip("Outlined", variant="outlined"),
            ),
        ),
        demo("divider", mui.divider(text="OR")),
        demo(
            "tooltip",
            mui.tooltip(mui.button("g_tt_btn", "Hover me"), title="A helpful tooltip"),
        ),
        demo(
            "list",
            mui.list(
                [
                    {"primary": "Inbox", "secondary": "12 new"},
                    {"primary": "Drafts", "secondary": "2"},
                    {"primary": "Sent"},
                ]
            ),
        ),
        demo(
            "table",
            mui.table(
                ["Name", "Role", "Location"],
                [
                    ["Ada Lovelace", "Engineer", "London"],
                    ["Linus Torvalds", "Engineer", "Portland"],
                    ["Grace Hopper", "Admiral", "New York"],
                ],
            ),
        ),
        demo("stepper", mui.stepper(["Cart", "Address", "Payment"], active=1)),
        demo(
            "breadcrumbs",
            mui.breadcrumbs(
                [
                    {"label": "Home", "href": "#"},
                    {"label": "Library", "href": "#"},
                    {"label": "Data"},
                ]
            ),
        ),
        demo("link", mui.link("A navigation link", href="#")),
        demo(
            "image_list",
            mui.image_list(
                [
                    {
                        "src": f"https://picsum.photos/seed/{i}/240/160",
                        "alt": f"img {i}",
                    }
                    for i in range(1, 7)
                ],
                cols=3,
            ),
        ),
    )


def feedback_section() -> object:
    return section(
        "Feedback",
        demo(
            "circular_progress",
            row(mui.circular_progress(), mui.circular_progress(value=70)),
        ),
        demo(
            "linear_progress",
            mui.linear_progress(),
            mui.linear_progress(value=60),
        ),
        demo(
            "skeleton — variants",
            mui.skeleton(variant="text"),
            mui.skeleton(variant="rectangular", width=240, height=80),
            mui.skeleton(variant="circular", width=44, height=44),
        ),
        demo(
            "backdrop (toggle shares the switch's input_id)",
            mui.switch("g_backdrop", label="Show backdrop"),
            mui.backdrop(
                "g_backdrop", mui.typography("Backdrop — click anywhere to dismiss")
            ),
        ),
        demo(
            "snackbar (toggle shares the switch's input_id)",
            mui.switch("g_snackbar", label="Show snackbar"),
            mui.snackbar("g_snackbar", message="Hello from an MUI snackbar"),
        ),
    )


def surfaces_section() -> object:
    return section(
        "Surfaces",
        demo(
            "card", mui.card(mui.typography("Card body content."), title="Card title")
        ),
        demo(
            "paper",
            mui.paper(mui.typography("Paper surface (elevation 3)"), elevation=3),
        ),
        demo("app_bar", mui.app_bar(title="My Application")),
        demo(
            "accordion",
            mui.accordion(
                [
                    mui.accordion_item("a", "What is shinymui?"),
                    mui.accordion_item("b", "How do I add a component?"),
                ],
                mui.typography("MUI components wired to Shiny via shinyreact."),
                mui.typography("Use the /scaffold-component skill."),
            ),
        ),
    )


def overlays_section() -> object:
    return section(
        "Overlays & menus",
        demo(
            "dialog",
            mui.dialog(
                "g_dialog",
                mui.typography("Dialog body content goes here."),
                trigger_label="Open dialog",
                title="A dialog",
            ),
        ),
        demo(
            "drawer",
            mui.drawer(
                "g_drawer",
                mui.box(mui.typography("Drawer content")),
                trigger_label="Open drawer",
            ),
        ),
        demo(
            "menu",
            mui.menu(
                "g_menu",
                [
                    {"value": "edit", "label": "Edit"},
                    {"value": "duplicate", "label": "Duplicate"},
                    {"value": "delete", "label": "Delete"},
                ],
                trigger_label="Open menu",
            ),
        ),
        demo(
            "speed_dial",
            mui.box(
                mui.speed_dial(
                    "g_speeddial",
                    [
                        {"value": "copy", "label": "Copy"},
                        {"value": "share", "label": "Share"},
                        {"value": "print", "label": "Print"},
                    ],
                )
            ),
        ),
    )


def layout_section() -> object:
    return section(
        "Layout",
        demo(
            "stack (direction=row)",
            mui.stack(
                mui.chip("A"), mui.chip("B"), mui.chip("C"), direction="row", spacing=1
            ),
        ),
        demo(
            "grid",
            mui.grid(
                mui.paper(mui.typography("Cell 1")),
                mui.paper(mui.typography("Cell 2")),
                mui.paper(mui.typography("Cell 3")),
                spacing=2,
            ),
        ),
        demo(
            "button_group",
            mui.button_group(
                mui.button("g_bg1", "One"),
                mui.button("g_bg2", "Two"),
                mui.button("g_bg3", "Three"),
            ),
        ),
        demo("box", mui.box(mui.typography("A plain Box container."))),
        demo(
            "container",
            mui.container(mui.typography("A centered Container."), max_width="sm"),
        ),
    )


def server(input, output, session):
    @shinyreact.render_react
    def gallery():
        return mui.container(
            mui.stack(
                mui.typography("Material UI × shinyreact", variant="h4"),
                mui.typography(
                    "All 45 @mui/material components, wired to Shiny.",
                    variant="body2",
                    color="text.secondary",
                ),
                mui.divider(),
                inputs_section(),
                display_section(),
                feedback_section(),
                surfaces_section(),
                overlays_section(),
                layout_section(),
                spacing=4,
            ),
            max_width="lg",
        )


app = App(app_ui, server)
