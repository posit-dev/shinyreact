# shadcn feedback components. Generated split; edit here, then roxygenise.

#' A toast host. Mount once; the server pushes toasts to it via shadcn_toast().
#' @param message_type The send_message type this host listens for.
#' @param position Corner to show toasts in (default "bottom-right").
#' @param class Extra CSS classes merged onto the toaster element.
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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
#' @param ... Must be empty; forces later arguments to be passed by name.
#' @return A `shinyreact` node.
#' @export
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
