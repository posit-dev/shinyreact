# shadcn menus components. Generated split; edit here, then roxygenise.

#' A clickable menu action. Clicking it fires the menu's input.
#' @param value Identifier reported to the server when clicked.
#' @param label Text shown in the menu.
#' @param disabled Greys the item out and blocks clicks (default FALSE).
#' @param variant "default" or "destructive" (red, for delete actions).
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_menu_item <- function(value, label, ..., disabled = FALSE, variant = "default") {
  rlang::check_dots_empty()
  list(type = "item", value = value, label = label, disabled = disabled, variant = variant)
}

#' A non-interactive section header inside a menu.
#' @param label Header text.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_menu_label <- function(label, ...) {
  rlang::check_dots_empty()
  list(type = "label", label = label)
}

#' A divider line between menu sections.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_menu_separator <- function(...) {
  rlang::check_dots_empty()
  list(type = "separator")
}

#' A toggleable menu item with its own boolean Shiny input.
#' Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id for this checkbox's state.
#' @param label Text shown beside the checkmark.
#' @param checked Initial checked state (default FALSE).
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_menu_checkbox <- function(input_id, label, ..., checked = FALSE) {
  rlang::check_dots_empty()
  list(type = "checkbox", input_id = input_id, label = label, checked = checked)
}

#' A nested submenu. \code{...} are more menu_* builders (recursive).
#' @param label Text on the submenu trigger row.
#' @param ... The submenu's child items.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_menu_submenu <- function(label, ...) {
  list(type = "submenu", label = label, items = list(...))
}

#' A dropdown menu driven by an items data array.
#'
#' Clicking a menu_item sets input$<input_id> to a list(value=, nonce=) — the
#' nonce changes on every click so repeated clicks of the same item still
#' register. Pair with observeEvent(input$<input_id>, ignoreInit = TRUE).
#'
#' @param input_id Shiny input id for click events.
#' @param ... Menu contents, built with the shadcn_menu_* helpers.
#' @param trigger_label Label on the button that opens the menu (default "Open").
#' @param class Extra CSS classes merged onto the menu content panel.
#' @return A `shinyreact` node.
#' @export
shadcn_dropdown_menu <- function(input_id, ..., trigger_label = "Open", class = NULL) {
  node("shadcn:DropdownMenu", props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    items         = list(...),
    className     = class
  ))
}

#' A right-click context menu. Children = the trigger area; items = menu contents.
#'
#' Clicking a menu item sets input$<input_id> to list(value=, nonce=).
#' Use the shadcn_menu_* helpers to build items (same format as shadcn_dropdown_menu).
#'
#' @param input_id Shiny input id for click events.
#' @param ... The area the user right-clicks on (child nodes).
#' @param items Menu contents built with shadcn_menu_* helpers.
#' @param class Extra CSS classes merged onto the trigger wrapper.
#' @return A `shinyreact` node.
#' @export
shadcn_context_menu <- function(input_id, ..., items = list(), class = NULL) {
  node("shadcn:ContextMenu", ..., props = list(
    input_id  = input_id,
    items     = items,
    className = class
  ))
}

#' A single menu in a shadcn_menubar() (label + items).
#' @param label Text shown on the menu trigger in the bar.
#' @param ... Menu items built with shadcn_menu_* helpers.
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_menubar_menu <- function(label, ...) {
  list(label = label, items = list(...))
}

#' A horizontal menu bar. Clicking an item sets input$<input_id> to
#' list(menu=, value=, nonce=).
#' @param input_id Shiny input id for click events.
#' @param ... Menu specs built with shadcn_menubar_menu().
#' @param class Extra CSS classes merged onto the bar element.
#' @return A `shinyreact` node.
#' @export
shadcn_menubar <- function(input_id, ..., class = NULL) {
  node("shadcn:Menubar", props = list(
    input_id  = input_id,
    menus     = list(...),
    className = class
  ))
}

#' A navigation item for shadcn_navigation_menu().
#' @param label Text shown on the nav trigger.
#' @param href Optional link URL (plain link). Omit for dropdown triggers.
#' @param description Optional description shown in sub-item dropdowns.
#' @param items Optional list of sub-items (makes this a dropdown trigger).
#' @return A list describing the entry, consumed by its parent component.
#' @export
shadcn_nav_item <- function(label, href = NULL, description = NULL, items = NULL) {
  d <- list(label = label)
  if (!is.null(href)) d$href <- href
  if (!is.null(description)) d$description <- description
  if (!is.null(items)) d$items <- items
  d
}

#' A horizontal navigation bar. Data-driven from an items array.
#'
#' If input_id is provided, clicking a link fires input$<input_id> as
#' list(value=label, nonce=) instead of navigating.
#'
#' @param ... Nav items built with shadcn_nav_item().
#' @param input_id Optional Shiny input id for click tracking.
#' @param class Extra CSS classes merged onto the nav root.
#' @return A `shinyreact` node.
#' @export
shadcn_navigation_menu <- function(..., input_id = NULL, class = NULL) {
  node("shadcn:NavigationMenu", props = list(
    items     = list(...),
    input_id  = input_id,
    className = class
  ))
}
