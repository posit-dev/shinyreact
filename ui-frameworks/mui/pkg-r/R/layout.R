# Material UI layout/container components.

#' Material UI card
#'
#' A card container with an optional header title.
#' @param ... Child nodes rendered in the card body.
#' @param title Optional header title.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_card <- function(..., title = NULL, class = NULL) {
  node("mui:Card", ..., props = list(title = title, className = class))
}
