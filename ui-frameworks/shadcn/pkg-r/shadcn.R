# shadcn R helpers — Badge, Button, Card, Input, Separator.
# source() this from app.R, then call shadcn_dep() and the component helpers.

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

#' Display a small status badge.
#' @param text Badge label text.
#' @param variant "default", "secondary", or "outline".
shadcn_badge <- function(text, variant = "default") {
  node("shadcn:Badge", props = list(text = text, variant = variant))
}

#' An action button. Server reads input$<input_id> as a click counter.
#' @param input_id Shiny input id.
#' @param label Button label text.
#' @param variant "default", "outline", "secondary", or "ghost".
shadcn_button <- function(input_id, label, variant = "default") {
  node("shadcn:Button", props = list(input_id = input_id, label = label, variant = variant))
}

#' A card container with an optional header title.
#' @param title Optional card header text.
#' @param ... Child nodes rendered inside the card body.
shadcn_card <- function(title = NULL, ...) {
  props <- if (!is.null(title)) list(title = title) else list()
  node("shadcn:Card", ..., props = props)
}

#' A text input field. Server reads input$<input_id> as the current string.
#' @param input_id Shiny input id.
#' @param placeholder Placeholder text shown when the input is empty.
#' @param label Optional label displayed above the input.
#' @param debounce_ms Debounce delay in milliseconds (default 250).
shadcn_input <- function(input_id, placeholder = "", label = NULL, debounce_ms = 250) {
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
shadcn_separator <- function(orientation = "horizontal") {
  node("shadcn:Separator", props = list(orientation = orientation))
}

#' A dropdown select. Server reads input$<input_id> as the selected string.
#' @param input_id Shiny input id.
#' @param choices Character vector or list of \code{list(value=, label=)} items.
#' @param selected Initially selected value (defaults to first choice).
#' @param label Optional label displayed above the select.
shadcn_select <- function(input_id, choices, selected = NULL, label = NULL) {
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
shadcn_slider <- function(input_id, min = 0, max = 100, step = 1, value = 50, label = NULL) {
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
shadcn_switch <- function(input_id, label = NULL, checked = FALSE) {
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
shadcn_alert <- function(description, title = NULL, variant = "default") {
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
shadcn_checkbox <- function(input_id, label, checked = FALSE) {
  node("shadcn:Checkbox", props = list(
    input_id = input_id,
    label    = label,
    checked  = checked
  ))
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
