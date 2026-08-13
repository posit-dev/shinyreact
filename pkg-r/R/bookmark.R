# Bookmark restore. Uses Shiny internals for restore-context access (accepted
# per design spec docs/superpowers/specs/2026-05-26-r-package-design.md). The
# single wrapper `.restore_input_values()` is the ONLY place that touches
# shiny internals; if Shiny exposes a public API, replace just that function.
#
# SPIKE RESULT (shiny 1.13.0): The active restore context is reached via
# `shiny:::hasCurrentRestoreContext()` (guard) and
# `shiny:::getCurrentRestoreContext()`, which peeks `restoreCtxStack` and falls
# back to `getDefaultReactiveDomain()$restoreContext`. The context's `$input`
# field is a `shiny:::RestoreInputSet` R6 object. Its parsed input map lives in
# the private `values` environment.
#
# The non-destructive accessor is `ctx$input$asList()`, which is
# `as.list.environment(private$values, all.names = TRUE)` — a pure read that
# never touches `private$pending`/`private$used`. This mirrors Python's
# `ctx.input.as_dict()`. We must NOT use `restoreInput()` / `ctx$input$get()`:
# `get()` appends to `private$pending`, marking the value used and breaking the
# app's own `restoreInput()` calls in the same render. `all.names = TRUE` also
# preserves keys like `__proto__` that begin with a dot/are otherwise hidden.
# DESCRIPTION pins shiny >= 1.13.0 for these internals.

#' @keywords internal
.restore_input_values <- function() {
  # Return the parsed restore input values for the current request as a named
  # list, WITHOUT marking them used (mirrors Python ctx.input.as_dict()).
  # Returns list() when there is no active restore context (e.g. outside an
  # HTTP request, or no bookmark query string was parsed).
  tryCatch(
    {
      if (!shiny:::hasCurrentRestoreContext()) {
        return(list())
      }
      ctx <- shiny:::getCurrentRestoreContext()
      if (is.null(ctx) || is.null(ctx$input)) {
        return(list())
      }
      values <- ctx$input$asList()
      if (is.null(values)) list() else values
    },
    error = function(e) list()
  )
}

#' @keywords internal
restore_script_tag <- function() {
  values <- .restore_input_values()
  if (length(values) == 0L) {
    return(NULL)
  }
  # Layer 1: JSON of the values. `digits = NA` keeps full numeric precision --
  # jsonlite's default rounds doubles to 4 decimal places, which would silently
  # corrupt restored numeric values.
  json_payload <- as.character(jsonlite::toJSON(
    values,
    auto_unbox = TRUE,
    digits = NA
  ))
  # Neutralize "</" so the payload can't close the surrounding <script> tag.
  json_payload <- gsub("</", "<\\/", json_payload, fixed = TRUE)
  # Escape U+2028 / U+2029: legal in a JSON string, but JS line terminators and
  # therefore illegal inside a JS string literal. Python gets this for free from
  # `json.dumps(ensure_ascii = TRUE)`; `jsonlite::toJSON()` emits them as raw
  # UTF-8, which would produce an unparseable <script> block (issue #183).
  json_payload <- gsub("\u2028", "\\u2028", json_payload, fixed = TRUE)
  json_payload <- gsub("\u2029", "\\u2029", json_payload, fixed = TRUE)
  # Layer 2: wrap as a JS string literal (double-encode) so quotes/newlines
  # survive the JS parser before JSON.parse runs. `unbox()` states the scalar
  # contract explicitly instead of leaning on the `auto_unbox` heuristic.
  js_string_literal <- jsonlite::toJSON(jsonlite::unbox(json_payload))
  js <- paste0(
    "window.shinyreact = window.shinyreact || {};",
    "window.shinyreact._restore = JSON.parse(",
    js_string_literal,
    ");"
  )
  htmltools::tags$script(htmltools::HTML(js))
}
