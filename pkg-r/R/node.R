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

#' @rdname node
#' @param x A `shinyreact_node`.
#' @param ... Unused.
#' @exportS3Method htmltools::as.tags
as.tags.shinyreact_node <- function(x, ...) {
  parts <- serialize_ui(x)
  # Serialize script-safe so a payload containing "</script>" (or "<!--",
  # U+2028/U+2029, ...) cannot break out of the inline
  # <script type="application/json">. The escapes are decoded back by
  # JSON.parse on the client. See .script_safe_json() in wire.R.
  spec_json <- .script_safe_json(parts$payload)
  htmltools::tagList(
    shinyreact_dep(),
    parts$deps,
    htmltools::div(
      class = "shinyreact-static",
      htmltools::tags$script(
        htmltools::HTML(spec_json),
        type = "application/json"
      )
    )
  )
}
