# Material UI display components.

#' Material UI alert
#'
#' A status message. Display-only.
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

#' Material UI avatar
#'
#' An avatar with an optional image, alt text, and fallback text.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param src Image URL (optional).
#' @param alt Alternate text for the image.
#' @param text Fallback text shown when there's no image (usually initials).
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_avatar <- function(..., src = NULL, alt = NULL, text = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Avatar", props = list(
    src = src, alt = alt, text = text, className = class
  ))
}

#' Material UI badge
#'
#' Overlays a small badge on its children.
#' @param ... The element(s) the badge is overlaid on.
#' @param badge_content Content displayed inside the badge (e.g. a count).
#' @param color Badge color (e.g. "primary", "secondary", "error").
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_badge <- function(..., badge_content = NULL, color = "primary", class = NULL) {
  node("mui:Badge", ..., props = list(
    badge_content = badge_content, color = color, className = class
  ))
}

#' Material UI breadcrumbs
#'
#' A static breadcrumb trail from label/href items. Display-only.
#' @param items List of lists with `label` and optional `href`; the last is the
#'   current page.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_breadcrumbs <- function(items, ..., class = NULL) {
  rlang::check_dots_empty()
  node("mui:Breadcrumbs", props = list(items = items, className = class))
}

#' Material UI chip
#'
#' A compact label/tag chip. Display-only.
#' @param label Chip text.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param color Chip color (e.g. "default", "primary", "secondary").
#' @param variant MUI chip variant ("filled" or "outlined").
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_chip <- function(label, ..., color = "default", variant = "filled",
                     class = NULL) {
  rlang::check_dots_empty()
  node("mui:Chip", props = list(
    label = label, color = color, variant = variant, className = class
  ))
}

#' Material UI divider
#'
#' A separator line, optionally with inline text. Display-only.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param orientation "horizontal" or "vertical".
#' @param text Optional inline text shown within the divider.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_divider <- function(..., orientation = "horizontal", text = NULL,
                        class = NULL) {
  rlang::check_dots_empty()
  node("mui:Divider", props = list(
    orientation = orientation, text = text, className = class
  ))
}

#' Material UI image list
#'
#' A data-driven grid of images. Display-only.
#' @param items List of lists with `src` and optional `alt`.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param cols Number of columns in the grid.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_image_list <- function(items, ..., cols = 3, class = NULL) {
  rlang::check_dots_empty()
  node("mui:ImageList", props = list(items = items, cols = cols, className = class))
}

#' Material UI link
#'
#' A static link. Display-only.
#' @param label Link text.
#' @param href Destination URL.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param target Anchor target (e.g. "_blank").
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_link <- function(label, href, ..., target = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Link", props = list(
    label = label, href = href, target = target, className = class
  ))
}

#' Material UI list
#'
#' A list of items. With `input_id` the items become clickable.
#' @param items List of strings, or lists with `primary` and optional
#'   `secondary`.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param input_id When set, items become clickable and the server reads the
#'   selected item via `input$<input_id>`.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_list <- function(items, ..., input_id = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("mui:List", props = list(
    input_id = input_id, items = items, className = class
  ))
}

#' Material UI stepper
#'
#' A static stepper from an array of step labels. Display-only.
#' @param steps Step label strings.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param active Zero-based index of the active step.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_stepper <- function(steps, ..., active = 0, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Stepper", props = list(steps = steps, active = active, className = class))
}

#' Material UI table
#'
#' A static table from columns (header strings) and rows (arrays).
#' @param columns Character vector of header labels.
#' @param rows List of rows; each row a list of cell values.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_table <- function(columns, rows, ..., class = NULL) {
  rlang::check_dots_empty()
  node("mui:Table", props = list(columns = columns, rows = rows, className = class))
}

#' Material UI tooltip
#'
#' Wraps children with a hover tooltip.
#' @param ... The element(s) the user hovers over to see the tooltip.
#' @param title Text shown in the tooltip bubble.
#' @param class Extra CSS classes on the wrapping element.
#' @return A `shinyreact` node.
#' @export
mui_tooltip <- function(..., title = "", class = NULL) {
  node("mui:Tooltip", ..., props = list(title = title, className = class))
}

#' Material UI typography
#'
#' Text rendered with an MUI typography variant. Display-only.
#' @param text Text content.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param variant MUI typography variant (e.g. "h1", "body1").
#' @param align Text alignment (e.g. "left", "center", "right").
#' @param color Text color.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_typography <- function(text, ..., variant = "body1", align = NULL,
                           color = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Typography", props = list(
    text = text, variant = variant, align = align, color = color, className = class
  ))
}
