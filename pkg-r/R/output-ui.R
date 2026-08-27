# Extracting output UI from render functions (#203).
# See docs/superpowers/specs/2026-08-19-r-output-ui-extraction-design.md.

#' Extract the output UI for a Shiny render function
#'
#' Builds the HTML that a render function's matching `*Output()` function
#' would produce — e.g. `output_ui(renderText(...), "x")` is
#' `textOutput("x")` — without you having to know which output function that
#' is. The render function's expression is never evaluated; only its UI
#' constructor runs.
#'
#' This is the same `outputFunc` / `outputArgs` contract shiny itself uses in
#' `knit_print` and Express mode, and the R counterpart of the Python
#' renderer's `auto_output_ui()`. Its main use in shinyreact is dependency
#' extraction: `htmltools::findDependencies(output_ui(fn, id))` yields the
#' `htmlDependency` objects (binding JS/CSS) the output needs in the browser —
#' shinyreact does this automatically for every output registered in a live
#' session (see `install_dep_discovery()`).
#'
#' @param render_fn A Shiny render function (e.g. from [shiny::renderText()],
#'   `plotly::renderPlotly()`).
#' @param id Output id to build the UI for.
#' @return The output UI (a `shiny.tag`).
#' @noRd
output_ui <- function(render_fn, id) {
  if (!inherits(render_fn, "shiny.render.function")) {
    cli::cli_abort(
      "{.arg render_fn} must be a Shiny render function,
       not {.obj_type_friendly {render_fn}}."
    )
  }
  output_fn <- attr(render_fn, "outputFunc", exact = TRUE)
  if (!is.function(output_fn)) {
    cli::cli_abort(c(
      "{.arg render_fn} carries no {.code outputFunc} attribute to build UI
       from.",
      "i" = "{.fn shinyreact::reactive_output} render functions deliberately
             have none -- the React client owns their UI."
    ))
  }
  do.call(output_fn, c(list(id), attr(render_fn, "outputArgs", exact = TRUE)))
}

# `output_ui()` for harvest loops: NULL (skip) instead of an error for render
# functions without an outputFunc, such as reactive_output()'s.
output_ui_or_null <- function(render_fn, id) {
  if (
    !inherits(render_fn, "shiny.render.function") ||
      !is.function(attr(render_fn, "outputFunc", exact = TRUE))
  ) {
    return(NULL)
  }
  output_ui(render_fn, id)
}
