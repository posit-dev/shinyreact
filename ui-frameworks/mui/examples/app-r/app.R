library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
pkgload::load_all(file.path(app_dir, "../../pkg-r"), quiet = TRUE)
dep <- mui_dep()

ui <- page_react(
  tags$div(
    output_react("demo", extra_deps = list(dep)),
    output_react("echo"),
    style = paste(
      "max-width:560px; margin:2rem auto; padding:0 1rem;",
      "display:flex; flex-direction:column; gap:1rem;"
    )
  )
)

server <- function(input, output, session) {
  output$demo <- render_react({
    mui_card(
      mui_text_field("name", label = "Name", placeholder = "Your name…"),
      mui_slider("age", min = 18, max = 99, value = 30),
      mui_switch("subscribe", label = "Subscribe"),
      mui_checkbox("agree", label = "I agree"),
      mui_select("role", c("Engineer", "Designer", "PM"), label = "Role"),
      mui_button("save", "Save"),
      mui_dialog(
        "details",
        mui_alert("Dialog body content."),
        trigger_label = "Details",
        title = "Details"
      ),
      title = "shinymui demo"
    )
  })
  output$echo <- render_react({
    name <- input$name %||% ""
    mui_alert(
      sprintf(
        "Hi %s — age %s, role %s, saved %s times.",
        if (nzchar(name)) name else "there",
        input$age %||% 30, input$role %||% "-", input$save %||% 0
      ),
      severity = if (isTRUE(input$agree)) "success" else "info"
    )
  })
}

shinyApp(ui, server)
