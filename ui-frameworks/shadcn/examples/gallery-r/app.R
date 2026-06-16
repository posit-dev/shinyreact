# Component gallery — every shadcn x shinyreact component in one showcase.
# Each component sits in a labeled preview box, grouped into tabs. Every panel is
# live-wired. Mirrors examples/gallery-py/app.py.
# Run: shiny::runApp("ui-frameworks/shadcn/examples/gallery-r")

library(shiny)
library(shinyreact)

`%||%` <- function(a, b) if (is.null(a)) b else a

app_dir <- normalizePath(".")
pkgload::load_all(file.path(app_dir, "../../pkg-r"), quiet = TRUE)
dep <- shadcn_dep()

ui <- page_react(
  tags$div(
    output_react("gallery", extra_deps = list(dep)),
    style = "max-width:800px; margin:2.5rem auto; padding:0 1rem;"
  ),
  title = "shadcn x shinyreact gallery"
)

# A labeled preview box wrapping one component (shadcn-docs style).
demo <- function(label, ...) {
  tags$div(
    tags$div(
      label,
      class = "text-xs font-medium uppercase tracking-wide text-muted-foreground"
    ),
    tags$div(..., class = "flex flex-col gap-3"),
    class = "rounded-lg border p-4 flex flex-col gap-3"
  )
}

grid <- function(...) tags$div(..., class = "grid grid-cols-2 gap-4")
stack <- function(...) tags$div(..., class = "flex flex-col gap-4")

server <- function(input, output, session) {
  last_menu <- reactiveVal("none")
  last_menubar <- reactiveVal("-")
  last_ctx <- reactiveVal("-")

  observeEvent(input$menu_action, last_menu(input$menu_action$value),
    ignoreInit = TRUE
  )
  observeEvent(input$g_menubar,
    {
      sel <- input$g_menubar
      last_menubar(paste0(sel$menu, " -> ", sel$value))
    },
    ignoreInit = TRUE
  )
  observeEvent(input$g_ctx, last_ctx(input$g_ctx$value), ignoreInit = TRUE)
  observeEvent(input$toast_btn,
    {
      shadcn_toast(
        session, "Saved!",
        description = "Your settings were updated.", type = "success"
      )
    },
    ignoreInit = TRUE
  )

  # ---- panels -----------------------------------------------------------

  inputs_panel <- function() {
    picked <- input$g_date
    when <- if (!is.null(picked) && nzchar(picked)) {
      format(as.Date(picked), "%b %d, %Y")
    } else {
      "-"
    }
    stack(
      demo("Text input", shadcn_input("g_name", placeholder = "Your name...")),
      demo(
        "Select",
        shadcn_select(
          "g_fruit",
          choices = list(
            list(value = "apple", label = "Apple"),
            list(value = "banana", label = "Banana"),
            list(value = "cherry", label = "Cherry")
          ),
          selected = "apple"
        )
      ),
      demo(
        "Slider",
        shadcn_slider("g_level", min = 0, max = 100, step = 5, value = 40, label = "Level")
      ),
      grid(
        demo("Switch", shadcn_switch("g_notify", label = "Notifications", checked = TRUE)),
        demo("Checkbox", shadcn_checkbox("g_terms", label = "Accept terms"))
      ),
      demo("Calendar", shadcn_calendar("g_date")),
      demo(
        "Radio group",
        shadcn_radio_group(
          "g_fruit_radio",
          choices = c("Apple", "Banana", "Cherry"), selected = "Apple"
        )
      ),
      demo("OTP input", shadcn_input_otp("g_otp", length = 6L, separator = TRUE)),
      demo("Pagination", shadcn_pagination("g_page", total_pages = 10L, current = 1L)),
      shadcn_alert(
        sprintf(
          "name=%s | fruit=%s | level=%s | notify=%s | terms=%s | date=%s | otp=%s | page=%s",
          input$g_name %||% "(empty)", input$g_fruit %||% "apple",
          input$g_level %||% 40, input$g_notify %||% TRUE, input$g_terms %||% FALSE,
          when, input$g_otp %||% "(empty)", input$g_page %||% 1
        ),
        title = "Live input values"
      )
    )
  }

  display_panel <- function() {
    stack(
      grid(
        demo(
          "Badge",
          tags$div(
            shadcn_badge("default"),
            shadcn_badge("secondary", variant = "secondary"),
            shadcn_badge("outline", variant = "outline"),
            class = "flex gap-2 flex-wrap"
          )
        ),
        demo(
          "Tooltip",
          shadcn_tooltip(
            shadcn_badge("Hover me", variant = "secondary"),
            content = "This is a tooltip", side = "top"
          )
        )
      ),
      demo(
        "Alert",
        shadcn_alert("A neutral, informational message.", title = "Heads up"),
        shadcn_alert("Something needs your attention.", title = "Error", variant = "destructive")
      ),
      demo(
        "Hover card",
        shadcn_hover_card(
          shadcn_card(
            tags$div("@shadcn", class = "font-semibold"),
            tags$div("Building component libraries for React.", class = "text-sm text-muted-foreground")
          ),
          trigger_label = "@shadcn"
        )
      ),
      demo(
        "Table",
        shadcn_table(
          columns = c("Name", "Role", "Commits"),
          rows = list(
            list("Ada", "Author", 128L),
            list("Linus", "Maintainer", 4096L),
            list("Grace", "Reviewer", 64L)
          ),
          caption = "Contributor activity"
        )
      ),
      demo(
        "Empty state",
        shadcn_empty(
          shadcn_button("empty_btn", "Create item"),
          title = "No items yet",
          description = "Get started by creating your first item."
        )
      ),
      demo(
        "Chart - bar",
        shadcn_chart(
          data = list(
            list(month = "Jan", sales = 120L, returns = 20L),
            list(month = "Feb", sales = 180L, returns = 35L),
            list(month = "Mar", sales = 150L, returns = 28L),
            list(month = "Apr", sales = 210L, returns = 42L),
            list(month = "May", sales = 190L, returns = 31L),
            list(month = "Jun", sales = 240L, returns = 55L)
          ),
          series = list(
            shadcn_chart_series("sales", label = "Sales"),
            shadcn_chart_series("returns", label = "Returns")
          ),
          x_key = "month", type = "bar"
        )
      )
    )
  }

  actions_panel <- function() {
    stack(
      grid(
        demo("Button", shadcn_button("g_btn", "Click me")),
        demo(
          "Dropdown menu",
          shadcn_dropdown_menu(
            "menu_action",
            shadcn_menu_label("Actions"),
            shadcn_menu_item("edit", "Edit"),
            shadcn_menu_item("duplicate", "Duplicate"),
            shadcn_menu_submenu(
              "Move to",
              shadcn_menu_item("inbox", "Inbox"),
              shadcn_menu_item("archive", "Archive")
            ),
            shadcn_menu_separator(),
            shadcn_menu_item("delete", "Delete", variant = "destructive"),
            trigger_label = "Open menu"
          )
        ),
        demo(
          "Popover",
          shadcn_popover(
            "g_pop",
            shadcn_badge("Inside a popover"),
            shadcn_input("g_pop_text", placeholder = "Type here..."),
            trigger_label = "Open popover"
          )
        ),
        demo(
          "Dialog",
          shadcn_dialog(
            "g_dialog",
            shadcn_input("g_dialog_name", label = "Name"),
            shadcn_slider("g_dialog_age", min = 18, max = 99, value = 30, label = "Age"),
            trigger_label = "Open dialog",
            title = "Edit profile",
            description = "Make changes and close when done."
          )
        ),
        demo(
          "Alert dialog",
          shadcn_alert_dialog(
            "g_confirm",
            trigger_label = "Delete item",
            title = "Delete this item?",
            description = "This action cannot be undone.",
            confirm_label = "Delete"
          )
        ),
        demo(
          "Sheet",
          shadcn_sheet(
            "g_sheet",
            shadcn_input("g_sheet_name", label = "Name"),
            shadcn_slider("g_sheet_lvl", min = 0, max = 10, value = 5, label = "Priority"),
            trigger_label = "Open sheet",
            title = "Edit item",
            side = "right"
          )
        )
      ),
      shadcn_alert(
        sprintf(
          "button=%s clicks | last menu=%s | confirmed=%sx",
          input$g_btn %||% 0, last_menu(), input$g_confirm %||% 0
        ),
        title = "Live action state"
      )
    )
  }

  overlays_panel <- function() {
    stack(
      grid(
        demo(
          "Drawer",
          shadcn_drawer(
            "g_drawer",
            shadcn_badge("Drawer content"),
            shadcn_input("g_drawer_text", placeholder = "Type here..."),
            trigger_label = "Open drawer",
            title = "Drawer",
            direction = "bottom"
          )
        ),
        demo(
          "Context menu",
          shadcn_context_menu(
            "g_ctx",
            shadcn_card(
              tags$div(
                "Right-click here",
                class = "text-sm text-muted-foreground py-4 text-center"
              )
            ),
            items = list(
              shadcn_menu_item("copy", "Copy"),
              shadcn_menu_item("paste", "Paste"),
              shadcn_menu_separator(),
              shadcn_menu_item("delete", "Delete", variant = "destructive")
            )
          )
        )
      ),
      demo(
        "Scroll area",
        do.call(
          shadcn_scroll_area,
          c(
            lapply(1:24, function(i) {
              tags$div(shadcn_badge(paste("Item", i), variant = "outline"), class = "py-1")
            }),
            list(height = "180px")
          )
        )
      ),
      shadcn_alert(
        sprintf("Last context menu selection: %s", last_ctx()),
        title = "Context menu state"
      )
    )
  }

  navigation_panel <- function() {
    stack(
      demo(
        "Menubar",
        shadcn_menubar(
          "g_menubar",
          shadcn_menubar_menu(
            "File",
            shadcn_menu_item("new", "New"),
            shadcn_menu_item("open", "Open"),
            shadcn_menu_separator(),
            shadcn_menu_item("save", "Save")
          ),
          shadcn_menubar_menu(
            "Edit",
            shadcn_menu_item("undo", "Undo"),
            shadcn_menu_item("redo", "Redo"),
            shadcn_menu_separator(),
            shadcn_menu_item("cut", "Cut"),
            shadcn_menu_item("copy", "Copy"),
            shadcn_menu_item("paste", "Paste")
          )
        )
      ),
      demo(
        "Navigation menu",
        shadcn_navigation_menu(
          shadcn_nav_item(
            "Getting Started",
            items = list(
              shadcn_nav_item("Introduction", href = "#", description = "Re-usable components built with Radix."),
              shadcn_nav_item("Installation", href = "#", description = "How to install and configure.")
            )
          ),
          shadcn_nav_item(
            "Components",
            items = list(
              shadcn_nav_item("Button", href = "#"),
              shadcn_nav_item("Card", href = "#"),
              shadcn_nav_item("Dialog", href = "#")
            )
          ),
          shadcn_nav_item("About", href = "#")
        )
      ),
      demo(
        "Command palette",
        shadcn_command(
          "g_cmd",
          list(
            list(value = "calendar", label = "Calendar", group = "Suggestions"),
            list(value = "emoji", label = "Search Emoji", group = "Suggestions"),
            list(value = "calculator", label = "Calculator", group = "Suggestions"),
            list(value = "profile", label = "Profile", group = "Settings"),
            list(value = "billing", label = "Billing", group = "Settings"),
            list(value = "settings", label = "Settings", group = "Settings")
          ),
          placeholder = "Search commands..."
        )
      ),
      shadcn_alert(
        sprintf("menubar=%s | command=%s", last_menubar(), input$g_cmd %||% "(empty)"),
        title = "Navigation state"
      )
    )
  }

  layout_panel <- function() {
    stack(
      demo(
        "Carousel",
        shadcn_carousel(
          shadcn_card(tags$div("Slide 1", class = "p-8 text-center font-semibold")),
          shadcn_card(tags$div("Slide 2", class = "p-8 text-center font-semibold")),
          shadcn_card(tags$div("Slide 3", class = "p-8 text-center font-semibold"))
        )
      ),
      demo(
        "Resizable panels",
        shadcn_resizable(
          tags$div("Panel A", class = "flex items-center justify-center h-full text-sm"),
          tags$div("Panel B", class = "flex items-center justify-center h-full text-sm"),
          panels = list(list(default_size = 50L), list(default_size = 50L)),
          class = "h-32 rounded-lg border"
        )
      )
    )
  }

  feedback_panel <- function() {
    stack(
      shadcn_toaster(),
      demo(
        "Toast (server push)",
        shadcn_alert("Click below; the server pushes a toast notification."),
        shadcn_button("toast_btn", "Show toast")
      )
    )
  }

  # ---- assemble ---------------------------------------------------------

  output$gallery <- render_react({
    active <- input$gallery_tabs %||% "inputs"
    shadcn_card(
      tags$div(
        tags$div("Component Gallery", class = "text-lg font-semibold"),
        tags$div(
          "shadcn x shinyreact - 47 components, live-wired.",
          class = "text-sm text-muted-foreground"
        ),
        class = "flex flex-col gap-1"
      ),
      shadcn_tabs(
        "gallery_tabs",
        list(
          shadcn_tab("inputs", "Inputs"),
          shadcn_tab("display", "Display"),
          shadcn_tab("actions", "Actions"),
          shadcn_tab("overlays", "Overlays"),
          shadcn_tab("navigation", "Navigation"),
          shadcn_tab("layout", "Layout"),
          shadcn_tab("feedback", "Feedback")
        ),
        inputs_panel(),
        display_panel(),
        actions_panel(),
        overlays_panel(),
        navigation_panel(),
        layout_panel(),
        feedback_panel(),
        selected = "inputs"
      ),
      tags$div(
        shadcn_badge(sprintf("viewing: %s", active), variant = "secondary"),
        class = "flex"
      )
    )
  })
}

shinyApp(ui, server)
