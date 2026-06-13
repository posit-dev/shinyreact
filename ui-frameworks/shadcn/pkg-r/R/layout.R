# shadcn layout components. Generated split; edit here, then roxygenise.

#' A card container with an optional header title.
#' @param ... Child nodes rendered inside the card body.
#' @param title Optional card header text.
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_card <- function(..., title = NULL, class = NULL) {
  node("shadcn:Card", ..., props = list(title = title, className = class))
}

#' A single tab trigger spec for shadcn_tabs().
#' @param value Identifier for this tab (matches the active-tab input value).
#' @param label Text shown on the tab trigger.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_tab <- function(value, label, ...) {
  rlang::check_dots_empty()
  list(value = value, label = label)
}

#' A tabbed panel. `tabs` defines the triggers; `...` panels are the content.
#'
#' Panels are matched to tabs positionally — the Nth panel renders under the
#' Nth tab. Server reads input$<input_id> as the active tab's value.
#'
#' @param input_id Shiny input id for the active tab (two-way).
#' @param tabs List of tab trigger specs, built with shadcn_tab().
#' @param ... One content node per tab, in the same order as `tabs`.
#' @param selected Initially active tab value (defaults to the first tab).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_tabs <- function(input_id, tabs, ..., selected = NULL, class = NULL) {
  node("shadcn:Tabs", ..., props = list(
    input_id  = input_id,
    tabs      = tabs,
    selected  = selected,
    className = class
  ))
}

#' A disclosure: a trigger reveals/hides its children. Server reads
#' input$<input_id> as a boolean (open).
#' @param input_id Shiny input id.
#' @param ... Content shown when open.
#' @param trigger_label Label on the toggle button (default "Toggle").
#' @param open Initial open state (default FALSE).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_collapsible <- function(input_id, ..., trigger_label = "Toggle", open = FALSE,
                               class = NULL) {
  node("shadcn:Collapsible", ..., props = list(
    input_id = input_id, trigger_label = trigger_label, open = open, className = class
  ))
}

#' A resizable panel group. Children go in panels separated by drag handles.
#' @param ... Content nodes — each goes into one resizable panel.
#' @param orientation "horizontal" (side-by-side, default) or "vertical".
#' @param panels Optional list of list(default_size=%, min_size=%) per panel.
#' @param handle Show the grip icon on the resize handle (default TRUE).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_resizable <- function(..., orientation = "horizontal", panels = list(),
                             handle = TRUE, class = NULL) {
  node("shadcn:Resizable", ..., props = list(
    orientation = orientation,
    panels      = panels,
    handle      = handle,
    className   = class
  ))
}

#' A scrollable container. Children are the scroll content.
#' @param ... Content nodes rendered inside the scrollable area.
#' @param height CSS height string (default "300px").
#' @param orientation "vertical", "horizontal", or "both".
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_scroll_area <- function(..., height = "300px", orientation = "vertical", class = NULL) {
  node("shadcn:ScrollArea", ..., props = list(
    height = height, orientation = orientation, className = class
  ))
}

#' An accordion section header for shadcn_accordion() (value + title).
#' @param value Identifier for this section.
#' @param title Header text.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_accordion_item <- function(value, title) {
  list(value = value, title = title)
}

#' A vertical accordion. `items` are section headers; `...` panels are the
#' content, matched positionally. Server reads input$<input_id> as the open value(s).
#' @param input_id Shiny input id.
#' @param items List of section specs, built with shadcn_accordion_item().
#' @param ... One content node per item, in the same order.
#' @param type "single" (one open) or "multiple".
#' @param selected Initially open value(s).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
shadcn_accordion <- function(input_id, items, ..., type = "single", selected = NULL,
                             class = NULL) {
  node("shadcn:Accordion", ..., props = list(
    input_id = input_id, items = items, type = type, selected = selected,
    className = class
  ))
}
