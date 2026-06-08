library(shiny)
library(shinyreact)

src_dir <- normalizePath(".")
messages_dep <- htmltools::htmlDependency(
  name = "messages-example",
  version = as.character(as.integer(
    file.info(file.path(src_dir, "messages.js"))$mtime
  )),
  src = c(file = src_dir),
  script = list(src = "messages.js", defer = ""),
  stylesheet = "styles.css"
)

# ---------------------------------------------------------------------------
# Component helpers — thin wrappers around node() that mirror the
# registered JS components in messages.js.
# ---------------------------------------------------------------------------

app_layout <- function(title, ...) {
  node("AppLayout", ..., props = list(title = title))
}

toast_card <- function(title) {
  node("ToastCard", props = list(title = title))
}

# ---------------------------------------------------------------------------

ui <- output_react("main", extra_deps = list(messages_dep))

server <- function(input, output, session) {
  log_messages <- list(
    list(text = "User logged in", category = "info"),
    list(text = "File saved successfully", category = "success"),
    list(text = "Low disk space warning", category = "warning"),
    list(text = "Backup completed", category = "success"),
    list(text = "Processing data...", category = "info"),
    list(text = "Cache cleared", category = "info")
  )

  output$main <- render_react({
    app_layout(
      "Event Message Demo",
      toast_card("Toast messages from server")
    )
  })

  observe({
    invalidateLater(2000)
    log_event <- log_messages[[sample(length(log_messages), 1)]]
    send_message(session, "logEvent", log_event)
  })
}

shinyApp(ui, server)
