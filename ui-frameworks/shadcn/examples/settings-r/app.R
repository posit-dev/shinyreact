library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
pkgload::load_all(file.path(app_dir, "../../pkg-r"), quiet = TRUE)
dep <- shadcn_dep()

ui <- page_react(
  tags$div(
    output_react("prefs", extra_deps = list(dep)),
    style = "max-width:440px; margin:2rem auto; padding:0 1rem;"
  )
)

server <- function(input, output, session) {
  output$prefs <- render_react({
    name      <- if (!is.null(input$display_name) && nzchar(input$display_name)) input$display_name else ""
    theme     <- if (!is.null(input$theme)) input$theme else "system"
    font_size <- if (!is.null(input$font_size)) input$font_size else 14L
    notifs    <- isTRUE(input$notifications)
    newsletter <- isTRUE(input$newsletter)
    saves     <- if (!is.null(input$save_btn)) input$save_btn else 0L

    theme_variant <- switch(theme, light = "default", dark = "secondary", "outline")
    status <- if (saves > 0) {
      paste0("Saved ", saves, " time", if (saves != 1) "s" else "", ".")
    } else {
      "Make changes and save."
    }

    shadcn_card(
      shadcn_input("display_name", placeholder = "e.g. Ada Lovelace", label = "Display name"),
      shadcn_select(
        "theme",
        choices = list(
          list(value = "light", label = "Light"),
          list(value = "dark",  label = "Dark"),
          list(value = "system", label = "System default")
        ),
        selected = "system",
        label = "Color theme"
      ),
      shadcn_badge(theme, variant = theme_variant),
      shadcn_separator(),
      shadcn_slider("font_size", min = 10, max = 20, step = 1, value = 14, label = "Font size (px)"),
      shadcn_switch("notifications", label = "Enable notifications", checked = TRUE),
      shadcn_checkbox("newsletter", label = "Subscribe to newsletter"),
      shadcn_separator(),
      shadcn_button("save_btn", "Save preferences"),
      shadcn_alert(status, title = "Status"),
      title = "User Preferences"
    )
  })
}

shinyApp(ui, server)
