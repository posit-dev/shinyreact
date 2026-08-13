#' Send a custom message to client React components
#'
#' Messages are consumed by `useShinyMessageHandler(type, handler)` on the
#' React side. The `type` is namespaced to the current Shiny module (if any)
#' so module-scoped handlers match.
#'
#' @param session The Shiny session.
#' @param type Message type string; must match the `messageType` passed to
#'   `useShinyMessageHandler()` in the React component.
#' @param data Any JSON-serializable data.
#' @return Invisibly `NULL`.
#' @export
send_message <- function(session, type, data) {
  # Every Shiny session namespaces: `ShinySession$ns()` is `NS(NULL, id)` at
  # top level and the module prefix inside `moduleServer()`. Erroring beats the
  # old silent fallback to an un-namespaced type, which would deliver a message
  # no module-scoped handler matches (#184).
  if (!is.function(session$ns)) {
    cli::cli_abort(
      "{.arg session} must be a Shiny session object (no {.fun session$ns} found)."
    )
  }
  namespaced_type <- session$ns(type)
  session$sendCustomMessage(
    "shinyReactMessage",
    list(type = namespaced_type, data = data)
  )
  invisible(NULL)
}
