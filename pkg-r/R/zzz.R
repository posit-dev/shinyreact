.onLoad <- function(libname, pkgname) {
  shiny::registerInputHandler(
    "shinyreact.default",
    default_input_handler,
    force = TRUE
  )
  shiny::registerInputHandler(
    "shinyreact.asis",
    asis_input_handler,
    force = TRUE
  )
}
