#' Output placeholder for a shinyreact renderer
#'
#' Creates the `<div>` that the shinyreact Shiny output binding renders into.
#' Pair with [render_reactive()] on the server (assign to `output[[id]]`).
#'
#' @param id Output ID. Must match the server-side `output[[id]]` assignment.
#' @param extra_deps A list of [htmltools::htmlDependency] objects to include.
#'   Downstream packages use this to inject their own JS/CSS.
#' @return A `shiny.tag` `<div>`.
#' @export
ui_output <- function(id, extra_deps = list()) {
  do.call(
    htmltools::div,
    c(
      list(id = id, class = "shinyreact-output", shinyreact_dep()),
      extra_deps
    )
  )
}
