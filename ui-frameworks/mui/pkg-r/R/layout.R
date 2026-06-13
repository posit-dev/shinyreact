# Material UI layout components.

#' An MUI Box — a generic container that wraps its children.
#' @param ... Child nodes rendered inside the component.
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
mui_box <- function(..., class = NULL) {
  node("mui:Box", ..., props = list(className = class))
}

#' An MUI ButtonGroup — groups child buttons together.
#' @param ... Child nodes rendered inside the component.
#' @param variant Button style ("contained", "outlined", "text").
#' @param orientation "horizontal" or "vertical".
#' @param color Theme color ("primary", "secondary", etc.).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
mui_button_group <- function(..., variant = "contained", orientation = "horizontal",
                             color = "primary", class = NULL) {
  node("mui:ButtonGroup", ..., props = list(
    variant = variant, orientation = orientation, color = color, className = class
  ))
}

#' An MUI Container — centered, width-constrained layout wrapper.
#' @param ... Child nodes rendered inside the component.
#' @param max_width Max width breakpoint ("xs", "sm", "md", "lg", "xl").
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
mui_container <- function(..., max_width = "md", class = NULL) {
  node("mui:Container", ..., props = list(max_width = max_width, className = class))
}

#' An MUI Grid in container mode — lays out children on a grid.
#' @param ... Child nodes rendered inside the component.
#' @param spacing Gap between grid items (theme spacing units).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
mui_grid <- function(..., spacing = 2, class = NULL) {
  node("mui:Grid", ..., props = list(spacing = spacing, className = class))
}

#' An MUI Stack — lays out children along one axis.
#' @param ... Child nodes rendered inside the component.
#' @param direction "column" (vertical) or "row" (horizontal).
#' @param spacing Gap between items (theme spacing units).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
mui_stack <- function(..., direction = "column", spacing = 2, class = NULL) {
  node("mui:Stack", ..., props = list(
    direction = direction, spacing = spacing, className = class
  ))
}
