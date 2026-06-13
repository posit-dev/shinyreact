# Material UI feedback components.

#' A dimming overlay. Server reads `input$<input_id>` as the open state.
#'
#' Clicking the backdrop sets the input back to `FALSE`.
#' @param input_id Shiny input id holding the boolean open state.
#' @param ... Content rendered on top of the overlay (e.g. a spinner).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
mui_backdrop <- function(input_id, ..., class = NULL) {
  node("mui:Backdrop", ..., props = list(input_id = input_id, className = class))
}

#' A circular progress spinner. Display-only.
#' @param value Fill percentage, 0-100. `NULL` renders an indeterminate spinner.
#' @param color Theme color (e.g. "primary", "secondary", "success").
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
mui_circular_progress <- function(value = NULL, ..., color = "primary", class = NULL) {
  rlang::check_dots_empty()
  node("mui:CircularProgress", props = list(value = value, color = color, className = class))
}

#' A linear progress bar. Display-only.
#' @param value Fill percentage, 0-100. `NULL` renders an indeterminate bar.
#' @param color Theme color (e.g. "primary", "secondary", "success").
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
mui_linear_progress <- function(value = NULL, ..., color = "primary", class = NULL) {
  rlang::check_dots_empty()
  node("mui:LinearProgress", props = list(value = value, color = color, className = class))
}

#' A loading placeholder shape shown while content loads. Display-only.
#' @param variant Placeholder shape: "text", "rectangular", "rounded", or "circular".
#' @param width Placeholder width (pixels or CSS length).
#' @param height Placeholder height (pixels or CSS length).
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
mui_skeleton <- function(..., variant = "text", width = NULL, height = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Skeleton", props = list(
    variant   = variant,
    width     = width,
    height    = height,
    className = class
  ))
}

#' A transient notification. Server reads `input$<input_id>` as the open state.
#'
#' The snackbar sets the input back to `FALSE` when it auto-hides or closes.
#' @param input_id Shiny input id holding the boolean open state.
#' @param message Text shown in the snackbar.
#' @param auto_hide_ms Milliseconds before the snackbar auto-hides.
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
mui_snackbar <- function(input_id, ..., message = "", auto_hide_ms = 4000, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Snackbar", props = list(
    input_id     = input_id,
    message      = message,
    auto_hide_ms = auto_hide_ms,
    className    = class
  ))
}
