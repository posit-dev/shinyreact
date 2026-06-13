library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
pkgload::load_all(file.path(app_dir, "../../pkg-r"), quiet = TRUE)
dep <- shadcn_dep()

ui <- page_react(
  tags$div(
    output_react("demo_card", extra_deps = list(dep)),
    style = "max-width:520px; margin:2rem auto; padding:0 1rem;"
  )
)

server <- function(input, output, session) {
  output$demo_card <- render_react({
    name <- if (!is.null(input$my_input) && nzchar(input$my_input))
      input$my_input else ""
    clicks <- if (!is.null(input$my_btn)) input$my_btn else 0L
    color <- if (!is.null(input$color_select))
      input$color_select else "blue"
    brightness <- if (!is.null(input$brightness))
      input$brightness else 50L
    dark_mode <- isTRUE(input$dark_mode)
    agreed    <- isTRUE(input$agree)

    greeting <- if (nzchar(name))
      paste0("Hello, ", name, "!") else "Type your name above."
    status_variant <- if (!agreed) "destructive" else "default"
    status_msg <- if (!agreed) {
      "You must agree to the terms."
    } else {
      paste0("Welcome! Brightness: ", brightness, "%, Color: ", color)
    }

    shadcn_card(
      shadcn_input("my_input", placeholder = "Your name…", label = "Name"),
      shadcn_select(
        "color_select",
        choices  = c("blue", "green", "red", "purple"),
        selected = "blue",
        label    = "Favorite color"
      ),
      shadcn_slider(
        "brightness",
        min = 0, max = 100, step = 5, value = 50,
        label = "Brightness"
      ),
      shadcn_separator(),
      shadcn_switch("dark_mode", label = "Dark mode"),
      shadcn_checkbox("agree", label = "I agree to the terms"),
      shadcn_separator(),
      shadcn_button("my_btn", "Submit"),
      shadcn_separator(),
      shadcn_alert(status_msg, variant = status_variant),
      tags$div(
        shadcn_badge(greeting),
        shadcn_badge(paste0("clicked ", clicks, "×"), variant = "secondary"),
        class = "flex gap-2 flex-wrap"
      ),
      title = "shadcn demo"
    )
  })
}

shinyApp(ui, server)
