library(shiny)
library(shinyreact)

waiting <- faithful$waiting

# The whole page: Shiny's own dependencies plus this app's bundle, served as
# an htmlDependency out of www/. No shinyreact JS is injected — the client
# runtime is inside www/ui.js, built from the `@posit/shinyreact` copy that
# ships in this installed package. With no server-side bundle there is also no
# #shinyreact-config tag and no protocol handshake: one install owns both
# halves, so they cannot skew.
ui <- page_bare(
  page_react_dep("www", name = "npm-local"),
  title = "Old Faithful"
)

server <- function(input, output, session) {
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
