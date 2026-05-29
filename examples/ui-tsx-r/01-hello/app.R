library(shiny)
library(shinyreact)

ui <- page_react_html("www/index.html")

server <- function(input, output, session) {
  greeting <- reactive({
    name <- input$name
    if (is.null(name) || nchar(name) == 0) "World" else name
  })

  output$txtout_title <- render_reactive({
    paste0("Hello, ", greeting(), "!")
  })

  output$txtout_count <- render_reactive({
    input$click_count
  })
}

shinyApp(ui, server)
