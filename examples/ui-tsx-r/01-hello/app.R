library(shiny)
library(shinyreact)

ui <- page_react_html("www/index.html")

server <- function(input, output, session) {
  greeting <- reactive({
    name <- input$name
    if (is.null(name) || nchar(name) == 0) "World" else name
  })

  output$txtout_title <- reactive_output({
    paste0("Hello, ", greeting(), "!")
  })

  output$txtout_count <- reactive_output({
    input$click_count
  })
}

shinyApp(ui, server)
