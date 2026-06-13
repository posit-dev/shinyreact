# Material UI overlay components.

#' Material UI dialog
#'
#' A modal dialog. Server reads `input$<input_id>` as the boolean open state.
#' @param input_id Shiny input id tracking the open state.
#' @param ... Child nodes rendered in the dialog body.
#' @param trigger_label Text on the button that opens the dialog.
#' @param title Optional dialog title.
#' @param class Extra CSS classes on the dialog root.
#' @return A `shinyreact` node.
#' @export
mui_dialog <- function(input_id, ..., trigger_label = "Open", title = NULL,
                       class = NULL) {
  node("mui:Dialog", ..., props = list(
    input_id = input_id, trigger_label = trigger_label,
    title = title, className = class
  ))
}

#' Material UI drawer
#'
#' A sliding drawer. Server reads `input$<input_id>` as the boolean open state.
#' @param input_id Shiny input id tracking the open state.
#' @param ... Child nodes rendered inside the drawer.
#' @param trigger_label Text on the button that opens the drawer.
#' @param anchor Edge the drawer slides from: "left", "right", "top", or "bottom".
#' @param class Extra CSS classes on the drawer root.
#' @return A `shinyreact` node.
#' @export
mui_drawer <- function(input_id, ..., trigger_label = "Open", anchor = "left",
                       class = NULL) {
  node("mui:Drawer", ..., props = list(
    input_id = input_id, trigger_label = trigger_label,
    anchor = anchor, className = class
  ))
}

#' Material UI menu
#'
#' A dropdown menu. Server reads `input$<input_id>` as the picked `list(value=, nonce=)`.
#' @param input_id Shiny input id for click events.
#' @param items List of menu entries, each with `value` and `label`.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param trigger_label Text on the button that opens the menu.
#' @param class Extra CSS classes on the menu root.
#' @return A `shinyreact` node.
#' @export
mui_menu <- function(input_id, items, ..., trigger_label = "Open", class = NULL) {
  rlang::check_dots_empty()
  node("mui:Menu", props = list(
    input_id = input_id, items = items,
    trigger_label = trigger_label, className = class
  ))
}

#' Material UI speed dial
#'
#' A floating speed-dial. Server reads `input$<input_id>` as the picked
#' `list(value=, nonce=)`.
#' @param input_id Shiny input id for click events.
#' @param actions List of action entries, each with `value` and `label`.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @param class Extra CSS classes on the speed-dial root.
#' @return A `shinyreact` node.
#' @export
mui_speed_dial <- function(input_id, actions, ..., class = NULL) {
  rlang::check_dots_empty()
  node("mui:SpeedDial", props = list(
    input_id = input_id, actions = actions, className = class
  ))
}
