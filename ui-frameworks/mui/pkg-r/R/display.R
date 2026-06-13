# Material UI display components.

#' Material UI alert
#'
#' A status message.
#' @param text Message text.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param severity Alert severity: "error", "warning", "info", or "success".
#' @param variant MUI alert variant ("standard", "filled", "outlined").
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_alert <- function(text, ..., severity = "info", variant = "standard",
                      class = NULL) {
  rlang::check_dots_empty()
  node("mui:Alert", props = list(
    text = text, severity = severity, variant = variant, className = class
  ))
}
