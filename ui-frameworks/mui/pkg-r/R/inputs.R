# Material UI input components.

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
