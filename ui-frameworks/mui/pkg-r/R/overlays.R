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
