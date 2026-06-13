# shadcn overlays components. Generated split; edit here, then roxygenise.

#' A modal dialog. Trigger button opens it; server reads input$<input_id> as boolean.
#' @param input_id Shiny input id — TRUE while dialog is open.
#' @param ... Child nodes rendered inside the dialog body.
#' @param trigger_label Label on the button that opens the dialog (default "Open").
#' @param title Optional dialog title.
#' @param description Optional muted subtitle below the title.
#' @param class Extra CSS classes merged onto the dialog content panel.
#' @return A `shinyreact` node.
#' @export
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
#' @return A `shinyreact` node.
#' @export
shadcn_popover <- function(input_id, ..., trigger_label = "Open", align = "center",
                           class = NULL) {
  node("shadcn:Popover", ..., props = list(
    input_id      = input_id,
    trigger_label = trigger_label,
    align         = align,
    className     = class
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
#' @return A `shinyreact` node.
#' @export
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

#' A confirmation dialog. Server reads input$<confirm_id> as a click counter.
#' @param confirm_id Shiny input id incremented when the user confirms.
#' @param cancel_id Optional Shiny input id incremented on cancel.
#' @param trigger_label Label on the button that opens the dialog (default "Open").
#' @param title Dialog title (default "Are you sure?").
#' @param description Optional muted description text.
#' @param confirm_label Label on the confirm button (default "Continue").
#' @param cancel_label Label on the cancel button (default "Cancel").
#' @param class Extra CSS classes merged onto the dialog content panel.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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
#' @return A `shinyreact` node.
#' @export
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
