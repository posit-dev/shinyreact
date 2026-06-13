# shadcn inputs components. Generated split; edit here, then roxygenise.

#' An action button. Server reads input$<input_id> as a click counter.
#' @param input_id Shiny input id.
#' @param label Button label text.
#' @param variant default, secondary, destructive, outline, ghost, or link.
#' @param size "default", "sm", "lg", or "icon".
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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

#' A dropdown select. Server reads input$<input_id> as the selected string.
#' @param input_id Shiny input id.
#' @param choices Character vector or list of \code{list(value=, label=)} items.
#' @param selected Initially selected value (defaults to first choice).
#' @param label Optional label displayed above the select.
#' @param class Extra CSS classes merged onto the wrapper element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_switch <- function(input_id, ..., label = NULL, checked = FALSE, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Switch", props = list(
    input_id  = input_id,
    label     = label,
    checked   = checked,
    className = class
  ))
}

#' A checkbox. Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id.
#' @param label Label text shown beside the checkbox.
#' @param checked Initial checked state (default FALSE).
#' @param class Extra CSS classes merged onto the wrapper element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_checkbox <- function(input_id, label, ..., checked = FALSE, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Checkbox", props = list(
    input_id  = input_id,
    label     = label,
    checked   = checked,
    className = class
  ))
}

#' A multi-line text input. Server reads input$<input_id> as a string.
#' @param input_id Shiny input id.
#' @param placeholder Placeholder text shown when empty.
#' @param label Optional label displayed above the textarea.
#' @param debounce_ms Debounce delay in milliseconds (default 250).
#' @param class Extra CSS classes merged onto the wrapper element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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

#' A two-state toggle button. Server reads input$<input_id> as a boolean.
#' @param input_id Shiny input id.
#' @param label Text/aria-label shown on the toggle.
#' @param pressed Initial pressed state (default FALSE).
#' @param variant "default" or "outline".
#' @param size "default", "sm", or "lg".
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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

#' A single-select radio group. Server reads input$<input_id> as a string.
#' @param input_id Shiny input id.
#' @param choices Character vector or list of list(value=, label=) items.
#' @param selected Initially selected value (defaults to first choice).
#' @param label Optional label displayed above the group.
#' @param class Extra CSS classes merged onto the wrapper element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
shadcn_toggle_group <- function(input_id, choices, ..., type = "single", selected = NULL,
                                variant = "outline", size = "default", class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:ToggleGroup", props = list(
    input_id = input_id, choices = choices, type = type, selected = selected,
    variant = variant, size = size, className = class
  ))
}

#' A slide carousel. Children = the slide content (one child per slide).
#' @param ... Content nodes — each becomes one slide.
#' @param input_id Optional Shiny input id; set to 0-based current slide index.
#' @param orientation "horizontal" (default) or "vertical".
#' @param loop Whether the carousel loops at the ends (default FALSE).
#' @param class Extra CSS classes merged onto the root element.
#' @return A `shinyreact` node.
#' @export
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
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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

#' A command palette / filterable list. Server reads input$<input_id> as the
#' selected item's value string.
#' @param input_id Shiny input id.
#' @param items List of list(value=, label=, group=) items.
#'   group is optional — items with the same group appear under one heading.
#' @param placeholder Search input placeholder text (default "Search...").
#' @param empty_label Text shown when no items match (default "No results found.").
#' @param class Extra CSS classes merged onto the root element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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

#' A page-number pagination bar. Server reads input$<input_id> as integer (1-based).
#' @param input_id Shiny input id — current page number (1-based).
#' @param ... Must be empty (leaf component).
#' @param total_pages Total number of pages (default 10).
#' @param current Initially selected page (default 1).
#' @param show_ellipsis Collapse distant pages into ellipsis when TRUE.
#' @param class Extra CSS classes merged onto the nav element.
#' @return A `shinyreact` node.
#' @export
shadcn_pagination <- function(input_id, ..., total_pages = 10L, current = 1L,
                              show_ellipsis = TRUE, class = NULL) {
  rlang::check_dots_empty()
  node("shadcn:Pagination", props = list(
    input_id      = input_id,
    total_pages   = total_pages,
    current       = current,
    show_ellipsis = show_ellipsis,
    className     = class
  ))
}
