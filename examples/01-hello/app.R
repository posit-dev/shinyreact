library(shiny)
library(shinyreact)

# Base R ships the Old Faithful dataset; the Python servers read the same data
# from the faithful.csv exported next to this file.
waiting <- faithful$waiting

ui <- page_react() # discovers www/ui.js + www/ui.css

server <- function(input, output, session) {
  # input$bins is NULL until the client's first useShinyInput("bins", 30)
  # message arrives. Returning NULL leaves the React side on its "Loading…"
  # placeholder; req() would work too, but its silent error still reaches the
  # client. (Python's input.bins() raises a silent exception instead.)
  bins <- reactive(input$bins)

  output$dist_data <- reactive_output({
    n <- bins()
    if (is.null(n)) {
      return(NULL)
    }
    breaks <- seq(min(waiting), max(waiting), length.out = n + 1)
    h <- hist(waiting, breaks = breaks, plot = FALSE)
    # I() keeps length-1 vectors as JSON arrays (n = 1) instead of scalars.
    list(breaks = I(h$breaks), counts = I(h$counts))
  })

  output$dist_caption <- reactive_output({
    n <- bins()
    if (is.null(n)) {
      return(NULL)
    }
    paste0(
      length(waiting),
      " eruptions in ",
      n,
      " bin",
      if (n == 1) "" else "s"
    )
  })
}

shinyApp(ui, server)
