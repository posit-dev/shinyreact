library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
source(file.path(app_dir, "../../pkg-r/shadcn.R"))
dep <- shadcn_dep(file.path(app_dir, "../../www"))

ui <- page_react(
  tags$div(
    output_react("demo", extra_deps = list(dep)),
    style = "max-width:520px; margin:2rem auto; padding:0 1rem;"
  )
)

server <- function(input, output, session) {
  output$demo <- render_react({
    color         <- if (!is.null(input$color)) input$color else "blue"
    confirm_clicks <- if (!is.null(input$confirm_btn)) input$confirm_btn else 0L

    status <- if (confirm_clicks > 0) {
      paste0("Confirmed with ", color, "!")
    } else {
      "No confirmation yet."
    }

    color_variant <- switch(color, blue = "default", green = "secondary", "outline")

    shadcn_card(
      # Radix Select — real dropdown with checkmark and keyboard nav
      shadcn_select(
        "color",
        choices  = list(
          list(value = "blue",  label = "Blue"),
          list(value = "green", label = "Green"),
          list(value = "red",   label = "Red")
        ),
        selected = "blue",
        label    = "Favorite color"
      ),
      shadcn_badge(color, variant = color_variant),
      shadcn_separator(),

      # Popover — floating panel with child content
      shadcn_popover(
        "color_popover",
        shadcn_alert(paste("Color is", color), title = "Info"),
        shadcn_badge(color),
        trigger_label = "Color details"
      ),
      shadcn_separator(),

      # Dialog — modal with focus trap, child content, Close button
      shadcn_dialog(
        "info_dialog",
        shadcn_input("username", placeholder = "Your name…", label = "Name"),
        shadcn_slider("age", min = 18, max = 100, step = 1, value = 25, label = "Age"),
        shadcn_button("confirm_btn", "Confirm"),
        trigger_label = "Edit profile",
        title         = "Edit your profile",
        description   = "Update your details below."
      ),
      shadcn_alert(status, title = "Status"),
      title = "Overlay components"
    )
  })
}

shinyApp(ui, server)
