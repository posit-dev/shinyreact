library(shiny)
library(shinyreact)

src_dir <- normalizePath(".")
inputs_dep <- htmltools::htmlDependency(
  name = "inputs-example",
  version = as.character(as.integer(
    file.info(file.path(src_dir, "inputs.js"))$mtime
  )),
  src = c(file = src_dir),
  script = list(src = "inputs.js", defer = ""),
  stylesheet = "styles.css"
)

# ---------------------------------------------------------------------------
# Component helpers — thin wrappers around node() that mirror the
# registered JS components in inputs.js.
# ---------------------------------------------------------------------------

page_layout <- function(title, ...) {
  node("PageLayout", ..., props = list(title = title))
}

text_input_card <- function(
  input_id,
  output_id,
  default_value = "Hello, world!"
) {
  node(
    "TextInputCard",
    props = list(
      input_id = input_id,
      output_id = output_id,
      default_value = default_value
    )
  )
}

number_input_card <- function(input_id, output_id, default_value = 42) {
  node(
    "NumberInputCard",
    props = list(
      input_id = input_id,
      output_id = output_id,
      default_value = default_value
    )
  )
}

checkbox_input_card <- function(input_id, output_id, default_value = FALSE) {
  node(
    "CheckboxInputCard",
    props = list(
      input_id = input_id,
      output_id = output_id,
      default_value = default_value
    )
  )
}

radio_input_card <- function(input_id, output_id, default_value = "option1") {
  node(
    "RadioInputCard",
    props = list(
      input_id = input_id,
      output_id = output_id,
      default_value = default_value
    )
  )
}

select_input_card <- function(input_id, output_id, default_value = "apple") {
  node(
    "SelectInputCard",
    props = list(
      input_id = input_id,
      output_id = output_id,
      default_value = default_value
    )
  )
}

slider_input_card <- function(input_id, output_id, default_value = 50) {
  node(
    "SliderInputCard",
    props = list(
      input_id = input_id,
      output_id = output_id,
      default_value = default_value
    )
  )
}

date_input_card <- function(input_id, output_id) {
  node(
    "DateInputCard",
    props = list(input_id = input_id, output_id = output_id)
  )
}

button_input_card <- function(input_id, output_id) {
  node(
    "ButtonInputCard",
    props = list(input_id = input_id, output_id = output_id)
  )
}

file_input_card <- function(input_id, output_id) {
  node(
    "FileInputCard",
    props = list(input_id = input_id, output_id = output_id)
  )
}

batch_form_card <- function(input_id, output_id) {
  node(
    "BatchFormCard",
    props = list(input_id = input_id, output_id = output_id)
  )
}

# ---------------------------------------------------------------------------

ui <- output_react("main", extra_deps = list(inputs_dep))

server <- function(input, output, session) {
  output$main <- render_react({
    page_layout(
      "Shiny React Input Examples",
      text_input_card("txtin", "txtout"),
      number_input_card("numberin", "numberout"),
      checkbox_input_card("checkboxin", "checkboxout"),
      radio_input_card("radioin", "radioout"),
      select_input_card("selectin", "selectout"),
      slider_input_card("sliderin", "sliderout"),
      date_input_card("datein", "dateout"),
      button_input_card("buttonin", "buttonout"),
      file_input_card("filein", "fileout"),
      batch_form_card("batchdata", "batchout")
    )
  })

  output$txtout <- reactive_output({
    toupper(input$txtin)
  })

  output$numberout <- reactive_output({
    as.character(input$numberin)
  })

  output$checkboxout <- reactive_output({
    as.character(input$checkboxin)
  })

  output$radioout <- reactive_output({
    as.character(input$radioin)
  })

  output$selectout <- reactive_output({
    as.character(input$selectin)
  })

  output$sliderout <- reactive_output({
    as.character(input$sliderin)
  })

  output$dateout <- reactive_output({
    as.character(input$datein)
  })

  output$buttonout <- reactive_output({
    input$buttonin
    as.character(input$buttonin)
  })

  output$fileout <- reactive_output({
    files <- input$filein
    if (is.null(files) || length(files) == 0) {
      return(NULL)
    }
    # shinyreact's default input handler delivers the JS file-metadata array as
    # a clean list of records (one named list per file), matching Python's
    # list of dicts — so we can index each file's fields directly.
    summaries <- vapply(
      files,
      function(f) {
        size_kb <- round(as.numeric(f$size) / 1024, 1)
        type_str <- if (nzchar(f$type)) f$type else "unknown type"
        paste0(f$name, " (", size_kb, " KB, ", type_str, ")")
      },
      character(1)
    )
    paste(summaries, collapse = "\n")
  })

  output$batchout <- reactive_output({
    data <- input$batchdata
    if (is.null(data)) {
      return("No data submitted yet.")
    }
    data$receivedAt <- format(Sys.time(), "%Y-%m-%dT%H:%M:%OS3")
    data
  })
}

shinyApp(ui, server)
