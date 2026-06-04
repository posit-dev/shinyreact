# Built-in shinyreact input handlers, registered with shiny in .onLoad (zzz.R).
# See docs/superpowers/specs/2026-06-04-shinyreact-default-input-handler-design.md.

#' Default shinyreact input handler (internal)
#'
#' Applied to every untyped `useShinyInput` value. Preserves an array of objects
#' (an unnamed list whose every element is a named list) as a list of records,
#' matching Python's list-of-dicts. For all other shapes it reproduces shiny's
#' default no-type coercion: unnamed lists of scalars are flattened with
#' `unlist()`, everything else is returned as-is.
#' @keywords internal
default_input_handler <- function(value, session = NULL, name = NULL) {
  is_records <- is.list(value) &&
    is.null(names(value)) &&
    length(value) > 0 &&
    all(vapply(
      value,
      function(el) is.list(el) && !is.null(names(el)),
      logical(1)
    ))
  if (is_records) {
    return(value)
  }
  if (is.list(value) && is.null(names(value))) {
    return(unlist(value, recursive = TRUE))
  }
  value
}

#' As-is shinyreact input handler (internal)
#'
#' Opt-in via `type = "shinyreact.asis"`. Returns the parsed value completely
#' untouched (no flattening), for nested structures the default would coerce.
#' @keywords internal
asis_input_handler <- function(value, session = NULL, name = NULL) {
  value
}
