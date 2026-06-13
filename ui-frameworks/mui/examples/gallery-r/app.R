# Component gallery — every shinymui component and its variants in one showcase.
# Layout and spacing come from MUI's own components (Container, Stack with
# `spacing`, Card, Divider) since MUI has no Tailwind.
# Run: shiny::runApp("ui-frameworks/mui/examples/gallery-r")

library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
pkgload::load_all(file.path(app_dir, "../../pkg-r"), quiet = TRUE)
dep <- mui_dep()

# One labeled component demo: an overline caption above the component(s).
demo <- function(label, ...) {
  mui_stack(
    mui_typography(label, variant = "overline", color = "text.secondary"),
    ...,
    spacing = 1.5
  )
}

# Variants laid out horizontally with spacing.
row <- function(...) mui_stack(..., direction = "row", spacing = 2)

# A titled section: heading + a Card whose body stacks the demos.
section <- function(title, ...) {
  mui_stack(
    mui_typography(title, variant = "h5"),
    mui_card(mui_stack(..., spacing = 3)),
    spacing = 2
  )
}

inputs_section <- function() {
  section(
    "Inputs",
    demo(
      "button — variants & colors",
      row(
        mui_button("g_btn_contained", "Contained"),
        mui_button("g_btn_outlined", "Outlined", variant = "outlined"),
        mui_button("g_btn_text", "Text", variant = "text"),
        mui_button("g_btn_error", "Error", color = "error")
      )
    ),
    demo(
      "fab",
      row(
        mui_fab("g_fab1", "+"),
        mui_fab("g_fab2", "Go", color = "secondary", variant = "extended")
      )
    ),
    demo(
      "text_field — variants",
      mui_text_field("g_tf_outlined", label = "Outlined"),
      mui_text_field("g_tf_filled", label = "Filled", variant = "filled"),
      mui_text_field("g_tf_standard", label = "Standard", variant = "standard")
    ),
    demo("slider", mui_slider("g_slider", value = 30)),
    demo("rating", mui_rating("g_rating", max = 5)),
    demo(
      "switch / checkbox",
      row(
        mui_switch("g_switch", label = "Switch"),
        mui_checkbox("g_checkbox", label = "Checkbox")
      )
    ),
    demo(
      "radio_group",
      mui_radio_group("g_radio", c("One", "Two", "Three"), label = "Pick one")
    ),
    demo(
      "select",
      mui_select("g_select", c("Red", "Green", "Blue"), label = "Color")
    ),
    demo(
      "autocomplete",
      mui_autocomplete(
        "g_auto", c("Apple", "Banana", "Cherry", "Date"), label = "Fruit"
      )
    ),
    demo(
      "toggle_button_group",
      mui_toggle_button_group("g_tbg", c("left", "center", "right"))
    ),
    demo("pagination", mui_pagination("g_pag", count = 10)),
    demo(
      "bottom_navigation",
      mui_bottom_navigation("g_bn", list(
        list(value = "home", label = "Home"),
        list(value = "favorites", label = "Favorites"),
        list(value = "profile", label = "Profile")
      ))
    ),
    demo(
      "tabs",
      mui_tabs(
        "g_tabs",
        list(
          list(value = "a", label = "Tab A"),
          list(value = "b", label = "Tab B")
        ),
        mui_typography("Panel A content."),
        mui_typography("Panel B content.")
      )
    )
  )
}

display_section <- function() {
  section(
    "Display",
    demo(
      "typography — variants",
      mui_typography("h6 heading", variant = "h6"),
      mui_typography("Body text — the quick brown fox.", variant = "body1"),
      mui_typography("Caption text", variant = "caption")
    ),
    demo(
      "alert — severities",
      mui_alert("Success message", severity = "success"),
      mui_alert("Info message", severity = "info"),
      mui_alert("Warning message", severity = "warning"),
      mui_alert("Error message", severity = "error")
    ),
    demo(
      "avatar",
      row(mui_avatar(text = "AB"), mui_avatar(text = "CD"), mui_avatar(text = "EF"))
    ),
    demo("badge", mui_badge(mui_typography("Inbox"), badge_content = 4)),
    demo(
      "chip — variants",
      row(
        mui_chip("Default"),
        mui_chip("Primary", color = "primary"),
        mui_chip("Outlined", variant = "outlined")
      )
    ),
    demo("divider", mui_divider(text = "OR")),
    demo(
      "tooltip",
      mui_tooltip(mui_button("g_tt_btn", "Hover me"), title = "A helpful tooltip")
    ),
    demo(
      "list",
      mui_list(list(
        list(primary = "Inbox", secondary = "12 new"),
        list(primary = "Drafts", secondary = "2"),
        list(primary = "Sent")
      ))
    ),
    demo(
      "table",
      mui_table(
        c("Name", "Role", "Location"),
        list(
          c("Ada Lovelace", "Engineer", "London"),
          c("Linus Torvalds", "Engineer", "Portland"),
          c("Grace Hopper", "Admiral", "New York")
        )
      )
    ),
    demo("stepper", mui_stepper(c("Cart", "Address", "Payment"), active = 1)),
    demo(
      "breadcrumbs",
      mui_breadcrumbs(list(
        list(label = "Home", href = "#"),
        list(label = "Library", href = "#"),
        list(label = "Data")
      ))
    ),
    demo("link", mui_link("A navigation link", href = "#")),
    demo(
      "image_list",
      mui_image_list(
        lapply(1:6, function(i) {
          list(src = sprintf("https://picsum.photos/seed/%d/240/160", i),
               alt = paste("img", i))
        }),
        cols = 3
      )
    )
  )
}

feedback_section <- function() {
  section(
    "Feedback",
    demo(
      "circular_progress",
      row(mui_circular_progress(), mui_circular_progress(value = 70))
    ),
    demo(
      "linear_progress",
      mui_linear_progress(),
      mui_linear_progress(value = 60)
    ),
    demo(
      "skeleton — variants",
      mui_skeleton(variant = "text"),
      mui_skeleton(variant = "rectangular", width = 240, height = 80),
      mui_skeleton(variant = "circular", width = 44, height = 44)
    ),
    demo(
      "backdrop (toggle shares the switch's input_id)",
      mui_switch("g_backdrop", label = "Show backdrop"),
      mui_backdrop(
        "g_backdrop",
        mui_typography("Backdrop — click anywhere to dismiss")
      )
    ),
    demo(
      "snackbar (toggle shares the switch's input_id)",
      mui_switch("g_snackbar", label = "Show snackbar"),
      mui_snackbar("g_snackbar", message = "Hello from an MUI snackbar")
    )
  )
}

surfaces_section <- function() {
  section(
    "Surfaces",
    demo(
      "card",
      mui_card(mui_typography("Card body content."), title = "Card title")
    ),
    demo(
      "paper",
      mui_paper(mui_typography("Paper surface (elevation 3)"), elevation = 3)
    ),
    demo("app_bar", mui_app_bar(title = "My Application")),
    demo(
      "accordion",
      mui_accordion(
        list(
          mui_accordion_item("a", "What is shinymui?"),
          mui_accordion_item("b", "How do I add a component?")
        ),
        mui_typography("MUI components wired to Shiny via shinyreact."),
        mui_typography("Use the /scaffold-component skill.")
      )
    )
  )
}

overlays_section <- function() {
  section(
    "Overlays & menus",
    demo(
      "dialog",
      mui_dialog(
        "g_dialog",
        mui_typography("Dialog body content goes here."),
        trigger_label = "Open dialog",
        title = "A dialog"
      )
    ),
    demo(
      "drawer",
      mui_drawer(
        "g_drawer",
        mui_box(mui_typography("Drawer content")),
        trigger_label = "Open drawer"
      )
    ),
    demo(
      "menu",
      mui_menu(
        "g_menu",
        list(
          list(value = "edit", label = "Edit"),
          list(value = "duplicate", label = "Duplicate"),
          list(value = "delete", label = "Delete")
        ),
        trigger_label = "Open menu"
      )
    ),
    demo(
      "speed_dial",
      mui_box(mui_speed_dial(
        "g_speeddial",
        list(
          list(value = "copy", label = "Copy"),
          list(value = "share", label = "Share"),
          list(value = "print", label = "Print")
        )
      ))
    )
  )
}

layout_section <- function() {
  section(
    "Layout",
    demo(
      "stack (direction=row)",
      mui_stack(
        mui_chip("A"), mui_chip("B"), mui_chip("C"),
        direction = "row", spacing = 1
      )
    ),
    demo(
      "grid",
      mui_grid(
        mui_paper(mui_typography("Cell 1")),
        mui_paper(mui_typography("Cell 2")),
        mui_paper(mui_typography("Cell 3")),
        spacing = 2
      )
    ),
    demo(
      "button_group",
      mui_button_group(
        mui_button("g_bg1", "One"),
        mui_button("g_bg2", "Two"),
        mui_button("g_bg3", "Three")
      )
    ),
    demo("box", mui_box(mui_typography("A plain Box container."))),
    demo(
      "container",
      mui_container(mui_typography("A centered Container."), max_width = "sm")
    )
  )
}

ui <- page_react(
  tags$div(
    output_react("gallery", extra_deps = list(dep)),
    style = "margin: 2rem auto; max-width: 1040px; padding: 0 1rem;"
  ),
  title = "shinymui gallery"
)

server <- function(input, output, session) {
  output$gallery <- render_react({
    mui_container(
      mui_stack(
        mui_typography("Material UI × shinyreact", variant = "h4"),
        mui_typography(
          "All 45 @mui/material components, wired to Shiny.",
          variant = "body2", color = "text.secondary"
        ),
        mui_divider(),
        inputs_section(),
        display_section(),
        feedback_section(),
        surfaces_section(),
        overlays_section(),
        layout_section(),
        spacing = 4
      ),
      max_width = "lg"
    )
  })
}

shinyApp(ui, server)
