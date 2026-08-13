# Built-in shinyreact input handlers, registered with shiny in .onLoad (zzz.R).
# See docs/superpowers/specs/2026-06-04-shinyreact-default-input-handler-design.md.

#' Default shinyreact input handler (internal)
#'
#' Applied to every untyped `useShinyInput` value. Undoes the parts of
#' jsonlite/shiny simplification that make R disagree with Python about the same
#' JSON payload. Python needs no such handler — its deserializer never
#' simplifies (see `pkg-py/src/shinyreact/_input_handler.py`).
#'
#' The contract, stated in terms of the JSON the React hook sent:
#'
#' * **Array of objects** (`[{a: 1}, {b: 2}]`) — kept as a list of records,
#'   matching Python's list-of-dicts. This is the case shiny's default handler
#'   gets wrong.
#' * **Array of scalars** (`[0, 100]`, `["a", "b"]`) — flattened to an atomic
#'   vector, exactly as shiny does by default. The one deliberate divergence
#'   from Python, which yields a list; an atomic vector is what R code wants.
#' * **Empty array** (`[]`) — `list()`, matching Python's `[]`. Shiny's default
#'   yields `NULL`, conflating "empty" with "absent".
#' * **Array of arrays** (`[[1, 2], [3, 4]]`) — nesting preserved, matching
#'   Python. Shiny's default flattens it to `c(1, 2, 3, 4)`, which destroys the
#'   shape the component sent.
#' * Anything else — returned as-is.
#' @keywords internal
default_input_handler <- function(value, session = NULL, name = NULL) {
  if (!is.list(value) || !is.null(names(value))) {
    return(value)
  }
  # An empty JSON array is an empty array, not a missing value (Python: []).
  if (length(value) == 0L) {
    return(list())
  }
  # Flatten only a genuine array of scalars. Anything with a non-scalar element
  # -- a record, a nested array -- keeps its structure so R and Python hand the
  # component's payload back in the same shape.
  all_scalars <- all(vapply(
    value,
    function(el) is.atomic(el) && length(el) == 1L && is.null(names(el)),
    logical(1)
  ))
  if (all_scalars) {
    return(unlist(value, recursive = FALSE))
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
