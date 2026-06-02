library(shiny)
library(shinyreact)

ui <- page_react_html("www/index.html")

server <- function(input, output, session) {
  greeting <- reactive({
    name <- input$name
    if (is.null(name) || nchar(name) == 0) "World" else name
  })

  output$txtout_title <- render_react({
    paste0("Hello, ", greeting(), "!")
  })

  output$txtout_count <- render_react({
    input$click_count
  })
}

shinyApp(ui, server)
