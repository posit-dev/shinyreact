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
      "i" = "Shiny normally substitutes a placeholder constructor, so this is
             rare -- the render function was likely built without going through
             {.fn shiny::createRenderFunction}."
    ))
  }
  do.call(output_fn, c(list(id), attr(render_fn, "outputArgs", exact = TRUE)))
}

# `output_ui()` for harvest loops: NULL instead of an error when the render
# function carries no outputFunc at all.
#
# Note this is NOT the reactive_output() path: passing `outputFunc = NULL` to
# createRenderFunction() makes shiny substitute a placeholder constructor, so
# reactive_output()'s render functions DO have the attribute and build shiny's
# dep-less "<pre>No UI/output function provided</pre>". The harvest therefore
# builds that placeholder and finds zero dependencies, rather than skipping the
# output -- same end result, one wasted UI construction. Pinned by
# test-output-ui.R.
output_ui_or_null <- function(render_fn, id) {
  if (
    !inherits(render_fn, "shiny.render.function") ||
      !is.function(attr(render_fn, "outputFunc", exact = TRUE))
  ) {
    return(NULL)
  }
  output_ui(render_fn, id)
}
