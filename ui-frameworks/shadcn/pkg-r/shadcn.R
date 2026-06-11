# shadcn R helpers.
# source() this from app.R, then call shadcn_dep() and the component helpers.
#
# API convention (tidyverse-style, and consistent with shinyreact's node()):
#   * Required args come first, positionally (id, label, ...).
#   * For LEAF components, `...` is a keyword separator: everything after it
#     must be named, and rlang::check_dots_empty() rejects stray positional
#     args. This prevents positional misuse and lets new optional args be added
#     later without breaking existing calls.
#   * CONTAINER components (card, dialog, popover, tabs, dropdown_menu,
#     menu_submenu) keep `...` for CHILD nodes — mirroring node(type, ...).
#     Their optional scalars (title, trigger_label, ...) sit after `...`, so
#     they are keyword-only too. These do NOT call check_dots_empty().

#' HTMLDependency for the shadcn JS + CSS bundle.
#' @param www_dir Absolute path to ui-frameworks/shadcn/www/
shadcn_dep <- function(www_dir) {
  www_dir <- normalizePath(www_dir, mustWork = TRUE)
  js <- file.path(www_dir, "shadcn.js")
  mtime <- file.info(js)$mtime
  ver <- if (file.exists(js)) as.character(as.integer(mtime)) else "0"
  htmltools::htmlDependency(
    name       = "shinyshadcn",
    version    = ver,
    src        = c(file = www_dir),
    script     = list(src = "shadcn.js", defer = ""),
    stylesheet = "style.css"
  )
}

# --- Leaf components --------------------------------------------------------

#' Display a small status badge.
#' @param text Badge label text.
#' @param variant "default", "secondary", or "outline".
shadcn_badge <- function(text, ..., variant = "default") {
  rlang::check_dots_empty()
  node("shadcn:Badge", props = list(text = text, variant = variant))
}

#' An action button. Server reads input$<input_id> as a click counter.
#' @param input_id Shiny input id.
#' @param label Button label text.
#' @param variant "default", "outline", "secondary", or "ghost".
shadcn_button <- function(input_id, label, ..., variant = "default") {
  rlang::check_dots_empty()
  node("shadcn:Button", props = list(input_id = input_id, label = label, variant = variant))
}

#' A single-date picker. Server reads input$<input_id> as an ISO date string.
#' The value is "YYYY-MM-DD" (or NULL). Parse with as.Date(input$<input_id>).
#' @param input_id Shiny input id.
#' @param selected Initial date as an ISO string "YYYY-MM-DD".
shadcn_calendar <- function(input_id, ..., selected = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Calendar", props = list(input_id = input_id, selected = selected))
}

#' A text input field. Server reads input$<input_id> as the current string.
#' @param input_id Shiny input id.
#' @param placeholder Placeholder text shown when the input is empty.
#' @param label Optional label displayed above the input.
#' @param debounce_ms Debounce delay in milliseconds (default 250).
shadcn_input <- function(input_id, ..., placeholder = "", label = NULL, debounce_ms = 250) {
  rlang::check_dots_empty()
  node(
    "shadcn:Input",
    props = list(
      input_id    = input_id,
      placeholder = placeholder,
      label       = label,
      debounce_ms = debounce_ms
    )
  )
}

#' A thin rule line for visual separation.
#' @param orientation "horizontal" (default) or "vertical".
shadcn_separator <- function(..., orientation = "horizontal") {
  rlang::check_dots_empty()
  node("shadcn:Separator", props = list(orientation = orientation))
}

#' A dropdown select. Server reads input$<input_id> as the selected string.
#' @param input_id Shiny input id.
#' @param choices Character vector or list of \code{list(value=, label=)} items.
#' @param selected Initially selected value (defaults to first choice).
#' @param label Optional label displayed above the select.
shadcn_select <- function(input_id, choices, ..., selected = NULL, label = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Select", props = list(
    input_id = input_id,
    choices  = choices,
    selected = selected,
    label    = label
  ))
}

#' A numeric range slider. Server reads input$<input_id> as a number.
#' @param input_id Shiny input id.
#' @param min Minimum value (default 0).
#' @param max Maximum value (default 100).
#' @param step Step increment (default 1).
#' @param value Initial value (default 50).
#' @param label Optional label (shows current value on the right).
shadcn_slider <- function(input_id, ..., min = 0, max = 100, step = 1, value = 50, label = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Slider", props = list(
    input_id = input_id,
    min      = min,
    max      = max,
    step     = step,
    value    = value,
    label    = label
  ))
}

#' A toggle switch. Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id.
#' @param label Optional label shown beside the switch.
#' @param checked Initial checked state (default FALSE).
shadcn_switch <- function(input_id, ..., label = NULL, checked = FALSE) {
  rlang::check_dots_empty()
  node("shadcn:Switch", props = list(
    input_id = input_id,
    label    = label,
    checked  = checked
  ))
}

#' A status alert box. Display-only — no Shiny input.
#' @param description Alert body text.
#' @param title Optional bold title shown above the description.
#' @param variant "default" (neutral) or "destructive" (red, for errors/warnings).
shadcn_alert <- function(description, ..., title = NULL, variant = "default") {
  rlang::check_dots_empty()
  node("shadcn:Alert", props = list(
    title       = title,
    description = description,
    variant     = variant
  ))
}

#' A checkbox. Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id.
#' @param label Label text shown beside the checkbox.
#' @param checked Initial checked state (default FALSE).
shadcn_checkbox <- function(input_id, label, ..., checked = FALSE) {
  rlang::check_dots_empty()
  node("shadcn:Checkbox", props = list(
    input_id = input_id,
    label    = label,
    checked  = checked
  ))
}

#' A display-only data table. No Shiny input.
#' @param columns Character vector of header labels.
#' @param rows List of rows; each row a list of cell values.
#' @param caption Optional caption shown below the table.
shadcn_table <- function(columns, rows, ..., caption = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Table", props = list(columns = columns, rows = rows, caption = caption))
}

# --- Container components (`...` holds child nodes; no check_dots_empty) -----

#' A card container with an optional header title.
#' @param ... Child nodes rendered inside the card body.
#' @param title Optional card header text.
shadcn_card <- function(..., title = NULL) {
  props <- if (!is.null(title)) list(title = title) else list()
  node("shadcn:Card", ..., props = props)
}

#' A modal dialog. Trigger button opens it; server reads input$<input_id> as boolean.
#' @param input_id Shiny input id — TRUE while dialog is open.
#' @param ... Child nodes rendered inside the dialog body.
#' @param trigger_label Label on the button that opens the dialog (default "Open").
#' @param title Optional dialog title.
#' @param description Optional muted subtitle below the title.
shadcn_dialog <- function(input_id, ..., trigger_label = "Open", title = NULL, description = NULL) {
  node("shadcn:Dialog", ..., props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    title         = title,
    description   = description
  ))
}

#' A floating popover panel. Trigger button opens it; server reads input$<input_id> as boolean.
#' @param input_id Shiny input id — TRUE while popover is open.
#' @param ... Child nodes rendered inside the popover.
#' @param trigger_label Label on the button that opens the popover (default "Open").
#' @param align Horizontal alignment: "start", "center", or "end" (default "center").
shadcn_popover <- function(input_id, ..., trigger_label = "Open", align = "center") {
  node("shadcn:Popover", ..., props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    align         = align
  ))
}

# --- Dropdown menu (data-driven compound component) -------------------------
# A menu is a structured list of actions, so its contents are passed as a data
# array (`items`), not as nested nodes. The menu_* builders below are leaf
# helpers returning plain lists; shadcn_dropdown_menu / shadcn_menu_submenu are
# containers whose `...` collects those items.

#' A clickable menu action. Clicking it fires the menu's input.
#' @param value Identifier reported to the server when clicked.
#' @param label Text shown in the menu.
#' @param disabled Greys the item out and blocks clicks (default FALSE).
#' @param variant "default" or "destructive" (red, for delete actions).
shadcn_menu_item <- function(value, label, ..., disabled = FALSE, variant = "default") {
  rlang::check_dots_empty()
  list(type = "item", value = value, label = label, disabled = disabled, variant = variant)
}

#' A non-interactive section header inside a menu.
#' @param label Header text.
shadcn_menu_label <- function(label, ...) {
  rlang::check_dots_empty()
  list(type = "label", label = label)
}

#' A divider line between menu sections.
shadcn_menu_separator <- function(...) {
  rlang::check_dots_empty()
  list(type = "separator")
}

#' A toggleable menu item with its own boolean Shiny input.
#' Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id for this checkbox's state.
#' @param label Text shown beside the checkmark.
#' @param checked Initial checked state (default FALSE).
shadcn_menu_checkbox <- function(input_id, label, ..., checked = FALSE) {
  rlang::check_dots_empty()
  list(type = "checkbox", input_id = input_id, label = label, checked = checked)
}

#' A nested submenu. \code{...} are more menu_* builders (recursive).
#' @param label Text on the submenu trigger row.
#' @param ... The submenu's child items.
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
shadcn_dropdown_menu <- function(input_id, ..., trigger_label = "Open") {
  node("shadcn:DropdownMenu", props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    items         = list(...)
  ))
}

# --- Tabs (hybrid: trigger metadata + positional child panels) --------------

#' A single tab trigger spec for shadcn_tabs().
#' @param value Identifier for this tab (matches the active-tab input value).
#' @param label Text shown on the tab trigger.
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
shadcn_tabs <- function(input_id, tabs, ..., selected = NULL) {
  node("shadcn:Tabs", ..., props = list(
    input_id = input_id,
    tabs     = tabs,
    selected = selected
  ))
}

# --- Toaster (server-push, message-handler pattern) -------------------------
# A toast host has no input and no trigger — the server PUSHES toasts to it.
# Mount shadcn_toaster() once in the UI, then call shadcn_toast() from the
# server to display a notification.

#' A toast host. Mount once; the server pushes toasts to it via shadcn_toast().
#' @param message_type The send_message type this host listens for.
#' @param position Corner to show toasts in (default "bottom-right").
shadcn_toaster <- function(..., message_type = "toast", position = "bottom-right") {
  rlang::check_dots_empty()
  node("shadcn:Toaster", props = list(message_type = message_type, position = position))
}

#' Push a toast to a shadcn_toaster() host from the server.
#' @param session The Shiny session.
#' @param message The toast's main text.
#' @param description Optional secondary line.
#' @param type One of "default", "success", "info", "warning", "error", "loading".
#' @param duration Milliseconds to show the toast (sonner default if NULL).
#' @param message_type Must match the host's message_type.
shadcn_toast <- function(session, message, ..., description = NULL, type = "default",
                         duration = NULL, message_type = "toast") {
  rlang::check_dots_empty()
  send_message(session, message_type, list(
    message     = message,
    description = description,
    type        = type,
    duration    = duration
  ))
}
