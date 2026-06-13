# Material UI surface components.

#' An accordion section header for mui_accordion() (value + title).
#' @param value Identifier for this section.
#' @param title Header text.
#' @return A list describing an accordion item.
#' @export
mui_accordion_item <- function(value, title) {
  list(value = value, title = title)
}

#' Material UI accordion
#'
#' A vertical accordion. `items` are the section headers; `...` panels are the
#' panel bodies, matched positionally.
#' @param items List of section specs, built with mui_accordion_item().
#' @param ... Child nodes rendered inside the component.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_accordion <- function(items, ..., class = NULL) {
  node("mui:Accordion", ..., props = list(items = items, className = class))
}

#' Material UI app bar
#'
#' A top app bar with an optional title and trailing children.
#' @param ... Child nodes rendered inside the component.
#' @param title Optional title text.
#' @param position AppBar position (e.g. "static", "fixed").
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_app_bar <- function(..., title = NULL, position = "static", class = NULL) {
  node("mui:AppBar", ..., props = list(title = title, position = position, className = class))
}

#' Material UI card
#'
#' A card container with an optional header title.
#' @param ... Child nodes rendered inside the component.
#' @param title Optional header title.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_card <- function(..., title = NULL, class = NULL) {
  node("mui:Card", ..., props = list(title = title, className = class))
}

#' Material UI paper
#'
#' A Paper surface wrapping its children.
#' @param ... Child nodes rendered inside the component.
#' @param elevation Shadow depth of the surface.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_paper <- function(..., elevation = 1, class = NULL) {
  node("mui:Paper", ..., props = list(elevation = elevation, className = class))
}
