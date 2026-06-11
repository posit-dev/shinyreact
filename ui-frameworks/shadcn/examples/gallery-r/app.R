# Component gallery — every shadcn x shinyreact component in one showcase.
#
# Each component sits in a labeled preview box (like shadcn's own docs), grouped
# into tabs. Every panel is live-wired so you can interact and watch values update.
# Run: shiny::runApp("ui-frameworks/shadcn/examples/gallery-r")

library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
source(file.path(app_dir, "../../pkg-r/shadcn.R"))
dep <- shadcn_dep(file.path(app_dir, "../../www"))

ui <- page_react(
  tags$div(
    output_react("gallery", extra_deps = list(dep)),
    style = "max-width:720px; margin:2.5rem auto; padding:0 1rem;"
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

  observeEvent(input$menu_action, {
    last_menu(input$menu_action$value)
  }, ignoreInit = TRUE)

  observeEvent(input$toast_btn, {
    shadcn_toast(session, "Saved!",
      description = "Your settings were updated.", type = "success"
    )
  }, ignoreInit = TRUE)

  # ---- panels -------------------------------------------------------------

  inputs_panel <- function() {
    name   <- if (!is.null(input$g_name)) input$g_name else ""
    fruit  <- if (!is.null(input$g_fruit)) input$g_fruit else "apple"
    level  <- if (!is.null(input$g_level)) input$g_level else 40L
    notify <- isTRUE(input$g_notify)
    terms  <- isTRUE(input$g_terms)
    picked <- if (!is.null(input$g_date)) input$g_date else NULL
    when   <- if (!is.null(picked)) format(as.Date(picked), "%b %d, %Y") else "—"

    stack(
      demo("Text input", shadcn_input("g_name", placeholder = "Your name…")),
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
      shadcn_alert(
        paste0(
          "name=", if (nzchar(name)) name else "∅",
          " · fruit=", fruit, " · level=", level,
          " · notify=", notify, " · terms=", terms, " · date=", when
        ),
        title = "Live input values"
      )
    )
  }

  display_panel <- function() {
    stack(
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
        "Alert",
        shadcn_alert("A neutral, informational message.", title = "Heads up"),
        shadcn_alert("Something needs your attention.",
          title = "Error", variant = "destructive"
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
      )
    )
  }

  actions_panel <- function() {
    clicks <- if (!is.null(input$g_btn)) input$g_btn else 0L
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
            shadcn_input("g_pop_text", placeholder = "Type here…"),
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
        )
      ),
      shadcn_alert(
        paste0("button clicks=", clicks, " · last menu action=", last_menu()),
        title = "Live action state"
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

  # ---- assemble -----------------------------------------------------------

  output$gallery <- render_react({
    active <- if (!is.null(input$gallery_tabs)) input$gallery_tabs else "inputs"
    shadcn_card(
      tags$div(
        tags$div("Component Gallery", class = "text-lg font-semibold"),
        tags$div(
          "shadcn x shinyreact — every component, live-wired.",
          class = "text-sm text-muted-foreground"
        ),
        class = "flex flex-col gap-1"
      ),
      shadcn_tabs(
        "gallery_tabs",
        tabs = list(
          shadcn_tab("inputs", "Inputs"),
          shadcn_tab("display", "Display"),
          shadcn_tab("actions", "Actions"),
          shadcn_tab("feedback", "Feedback")
        ),
        inputs_panel(),
        display_panel(),
        actions_panel(),
        feedback_panel(),
        selected = "inputs"
      ),
      tags$div(
        shadcn_badge(paste0("viewing: ", active), variant = "secondary"),
        class = "flex"
      )
    )
  })
}

shinyApp(ui, server)
