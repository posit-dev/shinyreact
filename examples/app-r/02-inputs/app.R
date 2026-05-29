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

ui <- ui_output("main", extra_deps = list(inputs_dep))

server <- function(input, output, session) {
  output$main <- render_reactive({
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

  output$txtout <- render_reactive({
    toupper(input$txtin)
  })

  output$numberout <- render_reactive({
    as.character(input$numberin)
  })

  output$checkboxout <- render_reactive({
    as.character(input$checkboxin)
  })

  output$radioout <- render_reactive({
    as.character(input$radioin)
  })

  output$selectout <- render_reactive({
    as.character(input$selectin)
  })

  output$sliderout <- render_reactive({
    as.character(input$sliderin)
  })

  output$dateout <- render_reactive({
    as.character(input$datein)
  })

  output$buttonout <- render_reactive({
    input$buttonin
    as.character(input$buttonin)
  })

  output$fileout <- render_reactive({
    files <- input$filein
    if (is.null(files)) {
      return(NULL)
    }
    summaries <- vapply(
      files,
      function(f) {
        size_kb <- round(f$size / 1024, 1)
        type_str <- if (nchar(f$type) > 0) f$type else "unknown type"
        paste0(f$name, " (", size_kb, " KB, ", type_str, ")")
      },
      character(1)
    )
    paste(summaries, collapse = "\n")
  })

  output$batchout <- render_reactive({
    data <- input$batchdata
    if (is.null(data)) {
      return("No data submitted yet.")
    }
    data$receivedAt <- format(Sys.time(), "%Y-%m-%dT%H:%M:%OS3")
    data
  })
}

shinyApp(ui, server)
