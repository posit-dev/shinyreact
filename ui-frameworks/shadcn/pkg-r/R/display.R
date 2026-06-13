# shadcn display components. Generated split; edit here, then roxygenise.

#' Display a small status badge.
#' @param text Badge label text.
#' @param variant default, secondary, destructive, outline, ghost, or link.
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_badge <- function(text, ..., variant = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Badge", props = list(text = text, variant = variant, className = class))
}

#' A thin rule line for visual separation.
#' @param orientation "horizontal" (default) or "vertical".
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_separator <- function(..., orientation = "horizontal", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Separator", props = list(orientation = orientation, className = class))
}

#' A status alert box. Display-only — no Shiny input.
#' @param description Alert body text.
#' @param title Optional bold title shown above the description.
#' @param variant "default" (neutral) or "destructive" (red, for errors/warnings).
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_alert <- function(description, ..., title = NULL, variant = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Alert", props = list(
    title       = title,
    description = description,
    variant     = variant,
    className   = class
  ))
}

#' A display-only data table. No Shiny input.
#' @param columns Character vector of header labels.
#' @param rows List of rows; each row a list of cell values.
#' @param caption Optional caption shown below the table.
#' @param class Extra CSS classes merged onto the table element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_table <- function(columns, rows, ..., caption = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Table", props = list(
    columns = columns, rows = rows, caption = caption, className = class
  ))
}

#' A display-only text label.
#' @param text Label text.
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_label <- function(text, ..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Label", props = list(text = text, className = class))
}

#' A loading placeholder. Size it via `class` (e.g. "h-4 w-32"). No input.
#' @param class CSS classes setting the placeholder's size/shape.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_skeleton <- function(..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Skeleton", props = list(className = class))
}

#' A determinate progress bar. Display-only.
#' @param value Fill percentage, 0-100.
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_progress <- function(value = 0, ..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Progress", props = list(value = value, className = class))
}

#' A user avatar. Shows `src` if it loads, else the `fallback` initials.
#' @param src Image URL (optional).
#' @param fallback Text shown when there's no image (usually initials).
#' @param size "default", "sm", or "lg".
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_avatar <- function(..., src = NULL, fallback = "", size = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Avatar", props = list(
    src = src, fallback = fallback, size = size, className = class
  ))
}

#' A keyboard-key hint. Display-only.
#' @param text The key label (e.g. "Cmd+K").
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_kbd <- function(text, ..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Kbd", props = list(text = text, className = class))
}

#' A loading spinner. Size it via `class` (e.g. "size-6"). Display-only.
#' @param class CSS classes setting the spinner's size.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_spinner <- function(..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Spinner", props = list(className = class))
}

#' A fixed aspect-ratio container.
#' @param ... Content rendered inside (e.g. an image).
#' @param ratio Width / height (e.g. 16 / 9).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_aspect_ratio <- function(..., ratio = 1, class = NULL) {
  node("shadcn:AspectRatio", ..., props = list(ratio = ratio, className = class))
}

#' A breadcrumb item for shadcn_breadcrumb() (label + optional href).
#' @param label Item text.
#' @param href Optional link URL.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_crumb <- function(label, href = NULL) {
  list(label = label, href = href)
}

#' A breadcrumb trail. Display-only.
#' @param ... Items built with shadcn_crumb(); the last is the current page.
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_breadcrumb <- function(..., class = NULL) {
  node("shadcn:Breadcrumb", props = list(items = list(...), className = class))
}

#' A data series spec for shadcn_chart().
#' @param key Column name in the data list.
#' @param label Display name shown in legend/tooltip.
#' @param color CSS color string (e.g. "#4f46e5").
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_chart_series <- function(key, label = NULL, color = NULL) {
  list(key = key, label = label, color = color)
}

#' A recharts chart. Display-only — no Shiny input.
#' @param data List of row lists, e.g. list(list(month="Jan", sales=120), ...).
#' @param series Series specs built with shadcn_chart_series().
#' @param type "bar", "line", "area", or "pie" (default "bar").
#' @param x_key Data key used as x-axis labels or pie slice names (default "name").
#' @param height Chart height in pixels (default 300).
#' @param legend Show the legend (default TRUE).
#' @param grid Show the cartesian grid (default TRUE).
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_chart <- function(data, series, ..., type = "bar", x_key = "name",
                         height = 300, legend = TRUE, grid = TRUE, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Chart", props = list(
    type      = type,
    data      = data,
    series    = series,
    x_key     = x_key,
    height    = height,
    legend    = legend,
    grid      = grid,
    className = class
  ))
}

#' A hover tooltip. Children = the trigger element; content = tooltip text.
#' @param ... The element(s) the user hovers over to see the tooltip.
#' @param content Text shown in the tooltip bubble.
#' @param side Which side the tooltip appears on: "top", "right", "bottom", or "left".
#' @param class Extra CSS classes merged onto the tooltip content.
#' @return A `shinyreact` node.
#' @export
shadcn_tooltip <- function(..., content = "", side = "top", class = NULL) {
  node("shadcn:Tooltip", ..., props = list(
    content = content, side = side, className = class
  ))
}

#' A hover card. Children = card body; trigger_label = the trigger text.
#' @param ... Content nodes rendered inside the card panel.
#' @param trigger_label Text shown as the hover trigger link (default "Hover").
#' @param side Which side the card appears on (default "bottom").
#' @param align Horizontal alignment: "start", "center", or "end" (default "center").
#' @param class Extra CSS classes merged onto the card content panel.
#' @return A `shinyreact` node.
#' @export
shadcn_hover_card <- function(..., trigger_label = "Hover", side = "bottom",
                              align = "center", class = NULL) {
  node("shadcn:HoverCard", ..., props = list(
    trigger_label = trigger_label, side = side, align = align, className = class
  ))
}

#' An empty-state placeholder. Children are rendered as the action area.
#' @param ... Action nodes (e.g. a button) shown below the header.
#' @param title Bold heading text for the empty state.
#' @param description Muted description text below the title.
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_empty <- function(..., title = NULL, description = NULL, class = NULL) {
  node("shadcn:Empty", ..., props = list(
    title = title, description = description, className = class
  ))
}
