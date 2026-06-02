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
  # HACK (see #125): blanket-escape every "<" as the JSON unicode escape
  # < so a payload containing "</script>" can't break out of the inline
  # <script type="application/json">. < is valid JSON and JSON.parse()
  # decodes it back to "<", so the round-trip is lossless. This is a crude
  # post-serialization string replace (it over-escapes all "<", not just
  # "</"/"<!--", and ignores U+2028/U+2029); #125 tracks replacing it with a
  # proper script-safe serializer helper shared with Python's Node.tagify().
  spec_json <- gsub(
    "<",
    "\\u003c",
    as.character(jsonlite::toJSON(parts$payload, auto_unbox = FALSE)),
    fixed = TRUE
  )
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
