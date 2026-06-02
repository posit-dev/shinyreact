# Is this UI content to walk into the wire tree, or raw data to pass through?
# Internal S3 generic (mirrors as_wire's dispatch + Python's _should_walk).
#  - node/tag/taglist -> walk
#  - bare character (incl. HTML(), via the html->character class vector) -> raw
#    passthrough, matching Python where HTML subclasses str
#  - plain lists, numbers, unknown -> default FALSE (raw data for
#    useShinyOutputValue)
# Downstream may register should_walk.theirclass <- function(x) TRUE to opt
# their own top-level component class into walking.
should_walk <- function(value) UseMethod("should_walk")

#' @keywords internal
#' @exportS3Method
should_walk.default <- function(value) FALSE

#' @keywords internal
#' @exportS3Method
should_walk.character <- function(value) FALSE

#' @keywords internal
#' @exportS3Method
should_walk.shinyreact_node <- function(value) TRUE

#' @keywords internal
#' @exportS3Method
should_walk.shiny.tag <- function(value) TRUE

#' @keywords internal
#' @exportS3Method
should_walk.shiny.tag.list <- function(value) TRUE

# Value-transform shared by render_react() and its tests.
.render_transform <- function(value) {
  if (is.null(value)) {
    return(NULL)
  }
  if (should_walk(value)) {
    parts <- serialize_ui(value)
    if (length(parts$deps) > 0L) {
      nms <- paste(
        vapply(parts$deps, function(d) d$name, character(1)),
        collapse = ", "
      )
      cli::cli_warn(c(
        "shinyreact output returned content carrying HTMLDependency objects ({nms}) that cannot be injected after the page has rendered.",
        "i" = "Declare them up-front via {.code output_react(..., extra_deps = list(...))} or at the page level."
      ))
    }
    return(parts$payload)
  }
  value
}

#' Render a React component tree (or raw data) to a shinyreact output
#'
#' Server-side counterpart to `useShinyOutputValue()`. Assign to `output[[id]]`
#' where the UI has a matching [output_react()]. Accepts a [node()] tree (which may
#' interleave htmltools tags, `HTML()`, and strings) or any JSON-serializable
#' value (passed through unchanged).
#'
#' @param expr An expression returning a `node()` tree / htmltools content, or a
#'   JSON-serializable value.
#' @param env The environment in which to evaluate `expr`.
#' @param quoted Is `expr` already quoted?
#' @return A Shiny render function.
#' @export
render_react <- function(expr, env = parent.frame(), quoted = FALSE) {
  func <- shiny::installExprFunction(
    expr,
    "func",
    eval.env = env,
    quoted = quoted,
    label = "render_react"
  )
  shiny::createRenderFunction(
    func,
    function(value, session, name, ...) .render_transform(value),
    output_react
  )
}

#' Publish a reactive value to a shinyreact client (the `ui.tsx` pattern)
#'
#' Server-side counterpart to `useShinyOutputValue()`. Assign to `output[[id]]`;
#' a React client reads the value by id. Unlike [render_react()] there is no UI
#' placeholder — the client owns all UI. Accepts any JSON-serializable value
#' (passed through unchanged).
#'
#' @param expr An expression returning a JSON-serializable value.
#' @param env The environment in which to evaluate `expr`.
#' @param quoted Is `expr` already quoted?
#' @return A Shiny render function.
#' @export
reactive_output <- function(expr, env = parent.frame(), quoted = FALSE) {
  func <- shiny::installExprFunction(
    expr,
    "func",
    eval.env = env,
    quoted = quoted,
    label = "reactive_output"
  )
  shiny::createRenderFunction(
    func,
    function(value, session, name, ...) .render_transform(value)
  )
}
