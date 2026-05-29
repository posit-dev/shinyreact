# Internal: the value-transform shared by render_reactive() and its tests.
# Returns a plain nested list (Shiny serializes it). NULL stays NULL.
.render_transform <- function(value) {
  if (is.null(value)) {
    return(NULL)
  }
  to_spec(value)
}

#' Render a React component tree (or raw data) to a shinyreact output
#'
#' The server-side counterpart to `useShinyOutputValue()` on the React client.
#' Assign to `output[[id]]` where the UI has a matching [ui_output()].
#'
#' Accepts a [node()]/[spec()]/[element()] tree (flattened via [to_spec()]) or
#' any JSON-serializable value (passed through unchanged).
#'
#' @param expr An expression returning a `Node`/`Spec`/`Element` or a
#'   JSON-serializable value.
#' @param env The environment in which to evaluate `expr`.
#' @param quoted Is `expr` already quoted?
#' @return A Shiny render function.
#' @export
render_reactive <- function(expr, env = parent.frame(), quoted = FALSE) {
  func <- shiny::installExprFunction(
    expr,
    "func",
    eval.env = env,
    quoted = quoted,
    label = "render_reactive"
  )

  shiny::createRenderFunction(
    func,
    function(value, session, name, ...) {
      .render_transform(value)
    },
    ui_output
  )
}
