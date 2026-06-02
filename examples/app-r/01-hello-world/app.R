library(shiny)
library(shinyreact)

src_dir <- normalizePath(".")
hello_dep <- htmltools::htmlDependency(
  name = "hello-world",
  version = as.character(as.integer(
    file.info(file.path(src_dir, "hello_world.js"))$mtime
  )),
  src = c(file = src_dir),
  script = list(src = "hello_world.js", defer = ""),
  stylesheet = "styles.css"
)

# ---------------------------------------------------------------------------
# Component helpers — thin wrappers around node() that mirror the
# registered JS components in hello_world.js.
# ---------------------------------------------------------------------------

card <- function(title, ...) {
  node("Card", ..., props = list(title = title))
}

text_input <- function(
  input_id,
  default_value = "",
  placeholder = "",
  label = ""
) {
  node(
    "TextInput",
    props = list(
      input_id = input_id,
      default_value = default_value,
      placeholder = placeholder,
      label = label
    )
  )
}

hr_node <- function() {
  node("Divider")
}

input_display <- function(input_id, default_value = "", label = "") {
  node(
    "InputDisplay",
    props = list(
      input_id = input_id,
      default_value = default_value,
      label = label
    )
  )
}

output_display <- function(output_id, label = "") {
  node(
    "OutputDisplay",
    props = list(
      output_id = output_id,
      label = label
    )
  )
}

# ---------------------------------------------------------------------------

ui <- page_react(hello_dep, output_react("hello"))

server <- function(input, output, session) {
  output$hello <- render_react({
    card(
      "Hello Shiny React!",
      # tags$small() is a shiny.tag — the walker serialises it to a
      # {"type":"tag","name":"small",...} wire node, rendered as
      # React.createElement("small", ...). (Only htmltools::HTML() produces a
      # dangerouslySetInnerHTML node.)
      htmltools::tags$small("A shinyreact × htmltools demo"),
      text_input(
        "txtin",
        "Hello, world!",
        placeholder = "Enter your message here...",
        label = "Type something to send to Shiny server:"
      ),
      hr_node(),
      input_display(
        "txtin",
        default_value = "Hello, world!",
        label = "Client-side value:"
      ),
      output_display("txtout", label = "Response from Shiny server:")
    )
  })

  output$txtout <- reactive_output({
    toupper(input$txtin)
  })
}

shinyApp(ui, server)
