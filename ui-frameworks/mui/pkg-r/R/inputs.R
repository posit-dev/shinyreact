# Material UI input components.

#' Material UI autocomplete
#'
#' Server reads `input$<input_id>` as the selected option.
#' @param input_id Shiny input id.
#' @param options Character vector of option strings.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param label Floating label text on the input.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_autocomplete <- function(input_id, options, ..., label = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Autocomplete", props = list(
    input_id = input_id, options = options, label = label, className = class
  ))
}

#' Material UI bottom navigation
#'
#' Server reads `input$<input_id>` as the selected item value.
#' @param input_id Shiny input id.
#' @param items List of `list(value=, label=)` entries, one per action.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_bottom_navigation <- function(input_id, items, ..., class = NULL) {
  rlang::check_dots_empty()
  node("mui:BottomNavigation", props = list(
    input_id = input_id, items = items, className = class
  ))
}

#' Material UI button
#'
#' Server reads `input$<input_id>` as a click counter.
#' @param input_id Shiny input id.
#' @param label Button text.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param variant MUI button variant ("contained", "outlined", "text").
#' @param color MUI theme color ("primary", "secondary", "success", ...).
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_button <- function(input_id, label = "Button", ..., variant = "contained",
                       color = "primary", class = NULL) {
  rlang::check_dots_empty()
  node("mui:Button", props = list(
    input_id = input_id, label = label, variant = variant,
    color = color, className = class
  ))
}

#' Material UI checkbox
#'
#' Server reads `input$<input_id>` as a boolean.
#' @param input_id Shiny input id.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param label Optional label beside the checkbox.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_checkbox <- function(input_id, ..., label = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Checkbox", props = list(
    input_id = input_id, label = label, className = class
  ))
}

#' Material UI floating action button
#'
#' Server reads `input$<input_id>` as a click counter.
#' @param input_id Shiny input id.
#' @param label Button content (icon or text).
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param color MUI theme color ("primary", "secondary", "success", ...).
#' @param variant "circular" or "extended".
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_fab <- function(input_id, label = NULL, ..., color = "primary",
                    variant = "circular", class = NULL) {
  rlang::check_dots_empty()
  node("mui:Fab", props = list(
    input_id = input_id, label = label, color = color,
    variant = variant, className = class
  ))
}

#' Material UI pagination
#'
#' Server reads `input$<input_id>` as the current page number (1-based).
#' @param input_id Shiny input id.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param count Total number of pages (default 10).
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_pagination <- function(input_id, ..., count = 10L, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Pagination", props = list(
    input_id = input_id, count = count, className = class
  ))
}

#' Material UI radio group
#'
#' Server reads `input$<input_id>` as the selected value.
#' @param input_id Shiny input id.
#' @param choices A character vector of values, or a list of
#'   `list(value=, label=)` entries.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param label Optional label displayed above the group.
#' @param selected Initially selected value (defaults to first choice).
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_radio_group <- function(input_id, choices, ..., label = NULL, selected = NULL,
                            class = NULL) {
  rlang::check_dots_empty()
  node("mui:RadioGroup", props = list(
    input_id = input_id, choices = choices, label = label,
    selected = selected, className = class
  ))
}

#' Material UI rating
#'
#' Server reads `input$<input_id>` as the current rating number.
#' @param input_id Shiny input id.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param max Maximum number of stars (default 5).
#' @param precision Smallest increment a star can be selected at (default 1).
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_rating <- function(input_id, ..., max = 5L, precision = 1, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Rating", props = list(
    input_id = input_id, max = max, precision = precision, className = class
  ))
}

#' Material UI select
#'
#' Server reads `input$<input_id>` as the selected value.
#' @param input_id Shiny input id.
#' @param choices A character vector of values, or a list of
#'   `list(value=, label=)` entries.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param label Floating label text.
#' @param selected Initially selected value.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_select <- function(input_id, choices, ..., label = NULL, selected = NULL,
                       class = NULL) {
  rlang::check_dots_empty()
  node("mui:Select", props = list(
    input_id = input_id, choices = choices, label = label,
    selected = selected, className = class
  ))
}

#' Material UI slider
#'
#' Server reads `input$<input_id>` as a number.
#' @param input_id Shiny input id.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param min Minimum value.
#' @param max Maximum value.
#' @param step Step increment.
#' @param value Initial value.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_slider <- function(input_id, ..., min = 0, max = 100, step = 1,
                       value = 50, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Slider", props = list(
    input_id = input_id, min = min, max = max, step = step,
    value = value, className = class
  ))
}

#' Material UI switch
#'
#' Server reads `input$<input_id>` as a boolean.
#' @param input_id Shiny input id.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param label Optional label beside the switch.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_switch <- function(input_id, ..., label = NULL, class = NULL) {
  rlang::check_dots_empty()
  node("mui:Switch", props = list(
    input_id = input_id, label = label, className = class
  ))
}

#' Material UI tabs
#'
#' Server reads `input$<input_id>` as the selected tab value. The metadata in
#' `tabs` drives the bar; child nodes are the panels (one per tab, by position).
#' @param input_id Shiny input id.
#' @param tabs List of `list(value=, label=)` entries, one per tab.
#' @param ... Child nodes rendered inside the component.
#' @param selected Initially selected tab value (defaults to first tab).
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_tabs <- function(input_id, tabs, ..., selected = NULL, class = NULL) {
  node("mui:Tabs", ..., props = list(
    input_id = input_id, tabs = tabs, selected = selected, className = class
  ))
}

#' Material UI text field
#'
#' Server reads `input$<input_id>` as the current string.
#' @param input_id Shiny input id.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param label Floating label text.
#' @param placeholder Placeholder text.
#' @param variant MUI text-field variant ("outlined", "filled", "standard").
#' @param debounce_ms Debounce before sending keystrokes to the server.
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_text_field <- function(input_id, ..., label = NULL, placeholder = NULL,
                           variant = "outlined", debounce_ms = 250, class = NULL) {
  rlang::check_dots_empty()
  node("mui:TextField", props = list(
    input_id = input_id, label = label, placeholder = placeholder,
    variant = variant, debounce_ms = debounce_ms, className = class
  ))
}

#' Material UI toggle button group
#'
#' Server reads `input$<input_id>` as the selected value(s) — a string when
#' `exclusive` is TRUE, else a character vector.
#' @param input_id Shiny input id.
#' @param choices A character vector of values, or a list of
#'   `list(value=, label=)` entries.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param exclusive Allow only one active button when TRUE (default TRUE).
#' @param class Extra CSS classes on the root element.
#' @return A `shinyreact` node.
#' @export
mui_toggle_button_group <- function(input_id, choices, ..., exclusive = TRUE,
                                    class = NULL) {
  rlang::check_dots_empty()
  node("mui:ToggleButtonGroup", props = list(
    input_id = input_id, choices = choices, exclusive = exclusive, className = class
  ))
}
