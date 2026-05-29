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
  namespaced_type <- if (is.function(session$ns)) session$ns(type) else type
  session$sendCustomMessage(
    "shinyReactMessage",
    list(type = namespaced_type, data = data)
  )
  invisible(NULL)
}
