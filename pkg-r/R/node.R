#' Create a React component node
#'
#' A `node()` names a registered React component and its props/children.
#' Children may mix other `node()`s, htmltools tags (`tags$div(...)`),
#' `htmltools::HTML()`, strings, and numbers; serialization walks them into the
#' JSON wire tree. Mirrors Python `shinyreact.Node`.
#'
#' @param type Registered component name (single non-empty string).
#' @param ... Children: `node()`s, htmltools tags, `HTML()`, strings, numbers.
#' @param props Named list of props (or empty).
#' @return An object of class `shinyreact_node`.
#' @export
node <- function(type, ..., props = list()) {
  if (!is.character(type) || length(type) != 1L) {
    cli::cli_abort("{.arg type} must be a single string.")
  }
  if (is.na(type) || !nzchar(type)) {
    cli::cli_abort("{.arg type} must be a non-empty string.")
  }
  if (length(props) > 0L) {
    nms <- names(props)
    if (is.null(nms) || any(!nzchar(nms))) {
      cli::cli_abort("{.arg props} must be a named list.")
    }
  }
  structure(
    list(type = type, props = props, children = list(...)),
    class = "shinyreact_node"
  )
}
