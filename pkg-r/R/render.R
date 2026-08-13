#' Publish a reactive value to a shinyreact client (the `ui.tsx` pattern)
#'
#' Server-side counterpart to `useShinyOutputValue()`. Assign to `output[[id]]`;
#' a React client reads the value by id. There is no UI placeholder — the
#' client owns all UI. Accepts any JSON-serializable value (passed through
#' unchanged).
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
    function(value, session, name, ...) value
  )
}
