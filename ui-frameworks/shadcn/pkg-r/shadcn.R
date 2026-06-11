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
#   * Every component takes `class` (default NULL) — extra CSS classes merged
#     onto the component's root via cn() on the JS side.

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
#' @param variant default, secondary, destructive, outline, ghost, or link.
#' @param class Extra CSS classes merged onto the root element.
shadcn_badge <- function(text, ..., variant = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Badge", props = list(text = text, variant = variant, className = class))
}

#' An action button. Server reads input$<input_id> as a click counter.
#' @param input_id Shiny input id.
#' @param label Button label text.
#' @param variant default, secondary, destructive, outline, ghost, or link.
#' @param size "default", "sm", "lg", or "icon".
#' @param class Extra CSS classes merged onto the root element.
shadcn_button <- function(input_id, label, ..., variant = "default", size = "default",
                          class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Button", props = list(
    input_id = input_id, label = label, variant = variant, size = size, className = class
  ))
}

#' A single-date picker. Server reads input$<input_id> as an ISO date string.
#' The value is "YYYY-MM-DD" (or NULL). Parse with as.Date(input$<input_id>).
#' @param input_id Shiny input id.
#' @param selected Initial date as an ISO string "YYYY-MM-DD".
#' @param class Extra CSS classes merged onto the root element.
shadcn_calendar <- function(input_id, ..., selected = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Calendar", props = list(input_id = input_id, selected = selected, className = class))
}

#' A text input field. Server reads input$<input_id> as the current string.
#' @param input_id Shiny input id.
#' @param placeholder Placeholder text shown when the input is empty.
#' @param label Optional label displayed above the input.
#' @param debounce_ms Debounce delay in milliseconds (default 250).
#' @param class Extra CSS classes merged onto the wrapper element.
shadcn_input <- function(input_id, ..., placeholder = "", label = NULL,
                         debounce_ms = 250, class = NULL) {
  rlang::check_dots_empty()
  node(
    "shadcn:Input",
    props = list(
      input_id    = input_id,
      placeholder = placeholder,
      label       = label,
      debounce_ms = debounce_ms,
      className   = class
    )
  )
}

#' A thin rule line for visual separation.
#' @param orientation "horizontal" (default) or "vertical".
#' @param class Extra CSS classes merged onto the root element.
shadcn_separator <- function(..., orientation = "horizontal", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Separator", props = list(orientation = orientation, className = class))
}

#' A dropdown select. Server reads input$<input_id> as the selected string.
#' @param input_id Shiny input id.
#' @param choices Character vector or list of \code{list(value=, label=)} items.
#' @param selected Initially selected value (defaults to first choice).
#' @param label Optional label displayed above the select.
#' @param class Extra CSS classes merged onto the wrapper element.
shadcn_select <- function(input_id, choices, ..., selected = NULL, label = NULL,
                          class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Select", props = list(
    input_id  = input_id,
    choices   = choices,
    selected  = selected,
    label     = label,
    className = class
  ))
}

#' A numeric range slider. Server reads input$<input_id> as a number.
#' @param input_id Shiny input id.
#' @param min Minimum value (default 0).
#' @param max Maximum value (default 100).
#' @param step Step increment (default 1).
#' @param value Initial value (default 50).
#' @param label Optional label (shows current value on the right).
#' @param class Extra CSS classes merged onto the wrapper element.
shadcn_slider <- function(input_id, ..., min = 0, max = 100, step = 1, value = 50,
                          label = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Slider", props = list(
    input_id  = input_id,
    min       = min,
    max       = max,
    step      = step,
    value     = value,
    label     = label,
    className = class
  ))
}

#' A toggle switch. Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id.
#' @param label Optional label shown beside the switch.
#' @param checked Initial checked state (default FALSE).
#' @param class Extra CSS classes merged onto the wrapper element.
shadcn_switch <- function(input_id, ..., label = NULL, checked = FALSE, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Switch", props = list(
    input_id  = input_id,
    label     = label,
    checked   = checked,
    className = class
  ))
}

#' A status alert box. Display-only — no Shiny input.
#' @param description Alert body text.
#' @param title Optional bold title shown above the description.
#' @param variant "default" (neutral) or "destructive" (red, for errors/warnings).
#' @param class Extra CSS classes merged onto the root element.
shadcn_alert <- function(description, ..., title = NULL, variant = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Alert", props = list(
    title       = title,
    description = description,
    variant     = variant,
    className   = class
  ))
}

#' A checkbox. Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id.
#' @param label Label text shown beside the checkbox.
#' @param checked Initial checked state (default FALSE).
#' @param class Extra CSS classes merged onto the wrapper element.
shadcn_checkbox <- function(input_id, label, ..., checked = FALSE, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Checkbox", props = list(
    input_id  = input_id,
    label     = label,
    checked   = checked,
    className = class
  ))
}

#' A display-only data table. No Shiny input.
#' @param columns Character vector of header labels.
#' @param rows List of rows; each row a list of cell values.
#' @param caption Optional caption shown below the table.
#' @param class Extra CSS classes merged onto the table element.
shadcn_table <- function(columns, rows, ..., caption = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Table", props = list(
    columns = columns, rows = rows, caption = caption, className = class
  ))
}

# --- Container components (`...` holds child nodes; no check_dots_empty) -----

#' A card container with an optional header title.
#' @param ... Child nodes rendered inside the card body.
#' @param title Optional card header text.
#' @param class Extra CSS classes merged onto the root element.
shadcn_card <- function(..., title = NULL, class = NULL) {
  node("shadcn:Card", ..., props = list(title = title, className = class))
}

#' A modal dialog. Trigger button opens it; server reads input$<input_id> as boolean.
#' @param input_id Shiny input id — TRUE while dialog is open.
#' @param ... Child nodes rendered inside the dialog body.
#' @param trigger_label Label on the button that opens the dialog (default "Open").
#' @param title Optional dialog title.
#' @param description Optional muted subtitle below the title.
#' @param class Extra CSS classes merged onto the dialog content panel.
shadcn_dialog <- function(input_id, ..., trigger_label = "Open", title = NULL,
                          description = NULL, class = NULL) {
  node("shadcn:Dialog", ..., props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    title         = title,
    description   = description,
    className     = class
  ))
}

#' A floating popover panel. Trigger button opens it; server reads input$<input_id> as boolean.
#' @param input_id Shiny input id — TRUE while popover is open.
#' @param ... Child nodes rendered inside the popover.
#' @param trigger_label Label on the button that opens the popover (default "Open").
#' @param align Horizontal alignment: "start", "center", or "end" (default "center").
#' @param class Extra CSS classes merged onto the popover content panel.
shadcn_popover <- function(input_id, ..., trigger_label = "Open", align = "center",
                           class = NULL) {
  node("shadcn:Popover", ..., props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    align         = align,
    className     = class
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
#' @param class Extra CSS classes merged onto the menu content panel.
shadcn_dropdown_menu <- function(input_id, ..., trigger_label = "Open", class = NULL) {
  node("shadcn:DropdownMenu", props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    items         = list(...),
    className     = class
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
#' @param class Extra CSS classes merged onto the root element.
shadcn_tabs <- function(input_id, tabs, ..., selected = NULL, class = NULL) {
  node("shadcn:Tabs", ..., props = list(
    input_id  = input_id,
    tabs      = tabs,
    selected  = selected,
    className = class
  ))
}

# --- Toaster (server-push, message-handler pattern) -------------------------
# A toast host has no input and no trigger — the server PUSHES toasts to it.
# Mount shadcn_toaster() once in the UI, then call shadcn_toast() from the
# server to display a notification.

#' A toast host. Mount once; the server pushes toasts to it via shadcn_toast().
#' @param message_type The send_message type this host listens for.
#' @param position Corner to show toasts in (default "bottom-right").
#' @param class Extra CSS classes merged onto the toaster element.
shadcn_toaster <- function(..., message_type = "toast", position = "bottom-right",
                           class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Toaster", props = list(
    message_type = message_type, position = position, className = class
  ))
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

# --- More display / input components ----------------------------------------

#' A multi-line text input. Server reads input$<input_id> as a string.
#' @param input_id Shiny input id.
#' @param placeholder Placeholder text shown when empty.
#' @param label Optional label displayed above the textarea.
#' @param debounce_ms Debounce delay in milliseconds (default 250).
#' @param class Extra CSS classes merged onto the wrapper element.
shadcn_textarea <- function(input_id, ..., placeholder = "", label = NULL,
                            debounce_ms = 250, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Textarea", props = list(
    input_id    = input_id,
    placeholder = placeholder,
    label       = label,
    debounce_ms = debounce_ms,
    className   = class
  ))
}

#' A display-only text label.
#' @param text Label text.
#' @param class Extra CSS classes merged onto the root element.
shadcn_label <- function(text, ..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Label", props = list(text = text, className = class))
}

#' A loading placeholder. Size it via `class` (e.g. "h-4 w-32"). No input.
#' @param class CSS classes setting the placeholder's size/shape.
shadcn_skeleton <- function(..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Skeleton", props = list(className = class))
}

#' A determinate progress bar. Display-only.
#' @param value Fill percentage, 0-100.
#' @param class Extra CSS classes merged onto the root element.
shadcn_progress <- function(value = 0, ..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Progress", props = list(value = value, className = class))
}

#' A two-state toggle button. Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id.
#' @param label Text/aria-label shown on the toggle.
#' @param pressed Initial pressed state (default FALSE).
#' @param variant "default" or "outline".
#' @param size "default", "sm", or "lg".
#' @param class Extra CSS classes merged onto the root element.
shadcn_toggle <- function(input_id, label, ..., pressed = FALSE, variant = "default",
                          size = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Toggle", props = list(
    input_id = input_id,
    label    = label,
    pressed  = pressed,
    variant  = variant,
    size     = size,
    className = class
  ))
}

#' A user avatar. Shows `src` if it loads, else the `fallback` initials.
#' @param src Image URL (optional).
#' @param fallback Text shown when there's no image (usually initials).
#' @param size "default", "sm", or "lg".
#' @param class Extra CSS classes merged onto the root element.
shadcn_avatar <- function(..., src = NULL, fallback = "", size = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Avatar", props = list(
    src = src, fallback = fallback, size = size, className = class
  ))
}

#' A keyboard-key hint. Display-only.
#' @param text The key label (e.g. "Cmd+K").
#' @param class Extra CSS classes merged onto the root element.
shadcn_kbd <- function(text, ..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Kbd", props = list(text = text, className = class))
}

#' A loading spinner. Size it via `class` (e.g. "size-6"). Display-only.
#' @param class CSS classes setting the spinner's size.
shadcn_spinner <- function(..., class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Spinner", props = list(className = class))
}

#' A fixed aspect-ratio container.
#' @param ... Content rendered inside (e.g. an image).
#' @param ratio Width / height (e.g. 16 / 9).
#' @param class Extra CSS classes merged onto the root element.
shadcn_aspect_ratio <- function(..., ratio = 1, class = NULL) {
  node("shadcn:AspectRatio", ..., props = list(ratio = ratio, className = class))
}

#' A single-select radio group. Server reads input$<input_id> as a string.
#' @param input_id Shiny input id.
#' @param choices Character vector or list of list(value=, label=) items.
#' @param selected Initially selected value (defaults to first choice).
#' @param label Optional label displayed above the group.
#' @param class Extra CSS classes merged onto the wrapper element.
shadcn_radio_group <- function(input_id, choices, ..., selected = NULL, label = NULL,
                               class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:RadioGroup", props = list(
    input_id  = input_id,
    choices   = choices,
    selected  = selected,
    label     = label,
    className = class
  ))
}

#' A group of toggle buttons. Server reads input$<input_id> as the selected
#' value (string for "single", character vector for "multiple").
#' @param input_id Shiny input id.
#' @param choices Character vector or list of list(value=, label=) items.
#' @param type "single" (one active) or "multiple".
#' @param selected Initial value.
#' @param variant "default" or "outline".
#' @param size "default", "sm", or "lg".
#' @param class Extra CSS classes merged onto the root element.
shadcn_toggle_group <- function(input_id, choices, ..., type = "single", selected = NULL,
                                variant = "outline", size = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:ToggleGroup", props = list(
    input_id = input_id, choices = choices, type = type, selected = selected,
    variant = variant, size = size, className = class
  ))
}

#' A breadcrumb item for shadcn_breadcrumb() (label + optional href).
#' @param label Item text.
#' @param href Optional link URL.
shadcn_crumb <- function(label, href = NULL) {
  list(label = label, href = href)
}

#' A breadcrumb trail. Display-only.
#' @param ... Items built with shadcn_crumb(); the last is the current page.
#' @param class Extra CSS classes merged onto the root element.
shadcn_breadcrumb <- function(..., class = NULL) {
  node("shadcn:Breadcrumb", props = list(items = list(...), className = class))
}

#' A disclosure: a trigger reveals/hides its children. Server reads
#' input$<input_id> as a boolean (open).
#' @param input_id Shiny input id.
#' @param ... Content shown when open.
#' @param trigger_label Label on the toggle button (default "Toggle").
#' @param open Initial open state (default FALSE).
#' @param class Extra CSS classes merged onto the root element.
shadcn_collapsible <- function(input_id, ..., trigger_label = "Toggle", open = FALSE,
                               class = NULL) {
  node("shadcn:Collapsible", ..., props = list(
    input_id = input_id, trigger_label = trigger_label, open = open, className = class
  ))
}

#' A slide carousel. Children = the slide content (one child per slide).
#' @param ... Content nodes — each becomes one slide.
#' @param input_id Optional Shiny input id; set to 0-based current slide index.
#' @param orientation "horizontal" (default) or "vertical".
#' @param loop Whether the carousel loops at the ends (default FALSE).
#' @param class Extra CSS classes merged onto the root element.
shadcn_carousel <- function(..., input_id = NULL, orientation = "horizontal",
                            loop = FALSE, class = NULL) {
  node("shadcn:Carousel", ..., props = list(
    input_id    = input_id,
    orientation = orientation,
    loop        = loop,
    className   = class
  ))
}

#' A one-time password input. Server reads input$<input_id> as a string.
#' @param input_id Shiny input id.
#' @param length Number of OTP slots (default 6).
#' @param separator Show a dash separator between the two halves (default FALSE).
#' @param class Extra CSS classes merged onto the root element.
shadcn_input_otp <- function(input_id, ..., length = 6, separator = FALSE,
                             class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:InputOtp", props = list(
    input_id  = input_id,
    length    = length,
    separator = separator,
    className = class
  ))
}

#' A resizable panel group. Children go in panels separated by drag handles.
#' @param ... Content nodes — each goes into one resizable panel.
#' @param orientation "horizontal" (side-by-side, default) or "vertical".
#' @param panels Optional list of list(default_size=%, min_size=%) per panel.
#' @param handle Show the grip icon on the resize handle (default TRUE).
#' @param class Extra CSS classes merged onto the root element.
shadcn_resizable <- function(..., orientation = "horizontal", panels = list(),
                             handle = TRUE, class = NULL) {
  node("shadcn:Resizable", ..., props = list(
    orientation = orientation,
    panels      = panels,
    handle      = handle,
    className   = class
  ))
}

#' A data series spec for shadcn_chart().
#' @param key Column name in the data list.
#' @param label Display name shown in legend/tooltip.
#' @param color CSS color string (e.g. "#4f46e5").
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

#' A swipe drawer (vaul). Slides in from an edge; server reads input$<input_id> as boolean.
#' @param input_id Shiny input id — TRUE while the drawer is open.
#' @param ... Content nodes rendered inside the drawer.
#' @param trigger_label Label on the button that opens the drawer (default "Open").
#' @param direction Edge the drawer slides from: "bottom", "top", "right", or "left".
#' @param title Optional drawer header title.
#' @param description Optional muted description below the title.
#' @param class Extra CSS classes merged onto the drawer content panel.
shadcn_drawer <- function(input_id, ..., trigger_label = "Open", direction = "bottom",
                          title = NULL, description = NULL, class = NULL) {
  node("shadcn:Drawer", ..., props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    direction     = direction,
    title         = title,
    description   = description,
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
shadcn_menubar_menu <- function(label, ...) {
  list(label = label, items = list(...))
}

#' A horizontal menu bar. Clicking an item sets input$<input_id> to
#' list(menu=, value=, nonce=).
#' @param input_id Shiny input id for click events.
#' @param ... Menu specs built with shadcn_menubar_menu().
#' @param class Extra CSS classes merged onto the bar element.
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
shadcn_navigation_menu <- function(..., input_id = NULL, class = NULL) {
  node("shadcn:NavigationMenu", props = list(
    items     = list(...),
    input_id  = input_id,
    className = class
  ))
}

#' A command palette / filterable list. Server reads input$<input_id> as the
#' selected item's value string.
#' @param input_id Shiny input id.
#' @param items List of list(value=, label=, group=) items.
#'   group is optional — items with the same group appear under one heading.
#' @param placeholder Search input placeholder text (default "Search...").
#' @param empty_label Text shown when no items match (default "No results found.").
#' @param class Extra CSS classes merged onto the root element.
shadcn_command <- function(input_id, items, ..., placeholder = "Search...",
                           empty_label = "No results found.", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Command", props = list(
    input_id    = input_id,
    items       = items,
    placeholder = placeholder,
    empty_label = empty_label,
    className   = class
  ))
}

#' A scrollable container. Children are the scroll content.
#' @param ... Content nodes rendered inside the scrollable area.
#' @param height CSS height string (default "300px").
#' @param orientation "vertical", "horizontal", or "both".
#' @param class Extra CSS classes merged onto the root element.
shadcn_scroll_area <- function(..., height = "300px", orientation = "vertical", class = NULL) {
  node("shadcn:ScrollArea", ..., props = list(
    height = height, orientation = orientation, className = class
  ))
}

#' A hover tooltip. Children = the trigger element; content = tooltip text.
#' @param ... The element(s) the user hovers over to see the tooltip.
#' @param content Text shown in the tooltip bubble.
#' @param side Which side the tooltip appears on: "top", "right", "bottom", or "left".
#' @param class Extra CSS classes merged onto the tooltip content.
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
shadcn_hover_card <- function(..., trigger_label = "Hover", side = "bottom",
                              align = "center", class = NULL) {
  node("shadcn:HoverCard", ..., props = list(
    trigger_label = trigger_label, side = side, align = align, className = class
  ))
}

#' A confirmation dialog. Server reads input$<confirm_id> as a click counter.
#' @param confirm_id Shiny input id incremented when the user confirms.
#' @param cancel_id Optional Shiny input id incremented on cancel.
#' @param trigger_label Label on the button that opens the dialog (default "Open").
#' @param title Dialog title (default "Are you sure?").
#' @param description Optional muted description text.
#' @param confirm_label Label on the confirm button (default "Continue").
#' @param cancel_label Label on the cancel button (default "Cancel").
#' @param class Extra CSS classes merged onto the dialog content panel.
shadcn_alert_dialog <- function(confirm_id, ..., cancel_id = NULL,
                                trigger_label = "Open", title = "Are you sure?",
                                description = NULL, confirm_label = "Continue",
                                cancel_label = "Cancel", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:AlertDialog", props = list(
    confirm_id    = confirm_id,
    cancel_id     = cancel_id,
    trigger_label = trigger_label,
    title         = title,
    description   = description,
    confirm_label = confirm_label,
    cancel_label  = cancel_label,
    className     = class
  ))
}

#' A side-panel sheet. Server reads input$<input_id> as boolean (open state).
#' @param input_id Shiny input id — TRUE while sheet is open.
#' @param ... Content nodes rendered inside the sheet.
#' @param trigger_label Label on the button that opens the sheet (default "Open").
#' @param side Edge the sheet slides from: "right", "left", "top", or "bottom".
#' @param title Optional sheet header title.
#' @param description Optional muted description below the title.
#' @param class Extra CSS classes merged onto the sheet content panel.
shadcn_sheet <- function(input_id, ..., trigger_label = "Open", side = "right",
                         title = NULL, description = NULL, class = NULL) {
  node("shadcn:Sheet", ..., props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    side          = side,
    title         = title,
    description   = description,
    className     = class
  ))
}

#' An accordion section header for shadcn_accordion() (value + title).
#' @param value Identifier for this section.
#' @param title Header text.
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
shadcn_accordion <- function(input_id, items, ..., type = "single", selected = NULL,
                             class = NULL) {
  node("shadcn:Accordion", ..., props = list(
    input_id = input_id, items = items, type = type, selected = selected,
    className = class
  ))
}
