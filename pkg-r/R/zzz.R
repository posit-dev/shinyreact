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
  shiny::registerInputHandler(
    "shinyreact.init",
    # Make sure outputs added have their dependencies sent to the client
    init_input_handler,
    force = TRUE
  )
}
