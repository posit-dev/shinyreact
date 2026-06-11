# Component gallery — every shadcn x shinyreact component in one app.
#
# Organized with Tabs into Inputs / Display / Actions / Feedback. Each panel is
# live-wired so you can interact and watch the reactive values update.
# Run: shiny::runApp("ui-frameworks/shadcn/examples/gallery-r")

library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
source(file.path(app_dir, "../../pkg-r/shadcn.R"))
dep <- shadcn_dep(file.path(app_dir, "../../www"))

ui <- page_react(
  tags$div(
    # Outer div is page chrome (htmltools, not React), so a string style is fine.
    # Inside render_react, use class = with Tailwind utilities — React rejects
    # string styles (error #62).
    output_react("gallery", extra_deps = list(dep)),
    style = "max-width:640px; margin:2rem auto; padding:0 1rem;"
  ),
  title = "shadcn x shinyreact gallery"
)

server <- function(input, output, session) {
  last_menu <- reactiveVal("none")

  observeEvent(input$g_menu, {
    last_menu(input$g_menu$value)
  }, ignoreInit = TRUE)

  observeEvent(input$g_toast, {
    shadcn_toast(
      session,
      "Saved!",
      description = "Your settings were updated.",
      type = "success"
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
    when   <- if (!is.null(picked)) format(as.Date(picked), "%b %d, %Y") else "none"

    tags$div(
      shadcn_input("g_name", placeholder = "Your name…", label = "Text input"),
      shadcn_select(
        "g_fruit",
        choices = list(
          list(value = "apple", label = "Apple"),
          list(value = "banana", label = "Banana"),
          list(value = "cherry", label = "Cherry")
        ),
        selected = "apple",
        label = "Select"
      ),
      shadcn_slider("g_level", min = 0, max = 100, step = 5, value = 40, label = "Slider"),
      shadcn_switch("g_notify", label = "Switch — notifications", checked = TRUE),
      shadcn_checkbox("g_terms", label = "Checkbox — accept terms"),
      shadcn_calendar("g_date"),
      shadcn_separator(),
      shadcn_alert(
        paste0(
          "name=", if (nzchar(name)) name else "∅",
          " · fruit=", fruit, " · level=", level,
          " · notify=", notify, " · terms=", terms, " · date=", when
        ),
        title = "Live input values"
      ),
      class = "flex flex-col gap-4"
    )
  }

  display_panel <- function() {
    tags$div(
      tags$div(
        shadcn_badge("default"),
        shadcn_badge("secondary", variant = "secondary"),
        shadcn_badge("outline", variant = "outline"),
        class = "flex gap-2"
      ),
      shadcn_alert("A neutral, informational message.", title = "Default alert"),
      shadcn_alert(
        "Something needs your attention.",
        title = "Destructive alert",
        variant = "destructive"
      ),
      shadcn_separator(),
      shadcn_table(
        columns = c("Name", "Role", "Commits"),
        rows = list(
          list("Ada", "Author", 128L),
          list("Linus", "Maintainer", 4096L),
          list("Grace", "Reviewer", 64L)
        ),
        caption = "Table — contributor activity"
      ),
      class = "flex flex-col gap-4"
    )
  }

  actions_panel <- function() {
    clicks <- if (!is.null(input$g_btn)) input$g_btn else 0L
    tags$div(
      tags$div(
        shadcn_button("g_btn", "Button"),
        shadcn_dropdown_menu(
          "g_menu",
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
          trigger_label = "Dropdown menu"
        ),
        class = "flex gap-2"
      ),
      tags$div(
        shadcn_popover(
          "g_pop",
          shadcn_badge("Inside a popover"),
          shadcn_input("g_pop_text", placeholder = "Type here…"),
          trigger_label = "Popover"
        ),
        shadcn_dialog(
          "g_dialog",
          shadcn_input("g_dialog_name", label = "Name"),
          shadcn_slider("g_dialog_age", min = 18, max = 99, value = 30, label = "Age"),
          trigger_label = "Dialog",
          title = "Edit profile",
          description = "Make changes and close when done."
        ),
        class = "flex gap-2"
      ),
      shadcn_separator(),
      shadcn_alert(
        paste0("button clicks=", clicks, " · last menu action=", last_menu()),
        title = "Live action state"
      ),
      class = "flex flex-col gap-4"
    )
  }

  feedback_panel <- function() {
    tags$div(
      shadcn_toaster(),
      shadcn_alert(
        "Click the button to have the server push a toast notification.",
        title = "Toast (server push)"
      ),
      shadcn_button("g_toast", "Show toast"),
      class = "flex flex-col gap-4"
    )
  }

  # ---- assemble -----------------------------------------------------------

  output$gallery <- render_react({
    active <- if (!is.null(input$gallery_tabs)) input$gallery_tabs else "inputs"
    shadcn_card(
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
      shadcn_separator(),
      tags$div(
        shadcn_badge(paste0("viewing: ", active), variant = "secondary"),
        class = "flex"
      ),
      title = "shadcn x shinyreact — Component Gallery"
    )
  })
}

shinyApp(ui, server)
