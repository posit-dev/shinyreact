library(shiny)
library(shinyreact)

# R counterpart of app.py over the same www/ client. plotly::renderPlotly's
# binding JS (htmlwidgets.js, plotly-binding) is discovered from the render
# function and pushed to the client automatically — no *Output() placeholder,
# no manual dependency wiring (#146/#203).

ui <- page_react_html("www/index.html")

server <- function(input, output, session) {
  output$greeting <- reactive_output({
    # NULL until the client's first useShinyInput message arrives; returning
    # NULL (not req()) keeps the silent-error noise out of the client console
    # -- same note as examples/01-hello/app.R.
    n <- input$num_points
    if (is.null(n)) {
      return(NULL)
    }
    sprintf("Showing %d random points", n)
  })

  output$scatter <- plotly::renderPlotly({
    n <- req(input$num_points)
    set.seed(42)
    fig <- plotly::plot_ly(
      x = rnorm(n),
      y = rnorm(n),
      type = "scatter",
      mode = "markers"
    )
    plotly::layout(
      fig,
      title = sprintf("Random Scatter (%d points)", n),
      margin = list(l = 40, r = 20, t = 40, b = 40)
    )
  })
}

shinyApp(ui, server)
