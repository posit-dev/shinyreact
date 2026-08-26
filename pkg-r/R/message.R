#' Send a custom message to client React components
#'
#' Messages are consumed by `useShinyMessageHandler(id, handler)` on the
#' React side. The `id` is namespaced to the current Shiny module (if any)
#' so module-scoped handlers match, just like input/output ids.
#'
#' @param session The Shiny session.
#' @param id Message id; must match the `id` passed to
#'   `useShinyMessageHandler()` in the React component.
#' @param data Any JSON-serializable data.
#' @return Invisibly `NULL`.
#' @export
send_message <- function(session, id, data) {
  # Every Shiny session namespaces: `ShinySession$ns()` is `NS(NULL, id)` at
  # top level and the module prefix inside `moduleServer()`. Erroring beats the
  # old silent fallback to an un-namespaced id, which would deliver a message
  # no module-scoped handler matches (#184).
  if (!is.function(session$ns)) {
    cli::cli_abort(
      "{.arg session} must be a Shiny session object (no {.fun session$ns} found)."
    )
  }
  namespaced_id <- session$ns(id)
  session$sendCustomMessage(
    "shinyReactMessage",
    list(id = namespaced_id, data = data)
  )
  invisible(NULL)
}
