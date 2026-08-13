# Bookmark restore. Uses Shiny internals (accepted per design spec
# docs/superpowers/specs/2026-05-26-r-package-design.md). Every use is confined
# to a named wrapper, so if Shiny exposes a public API only the wrapper changes:
#
#   shiny___has_current_restore_context()  -- restore-context guard
#   shiny___get_current_restore_context()  -- restore-context accessor
#   shiny___to_json()                      -- shiny's `toJSON()`, the serializer
#                                             Shiny uses for every value it
#                                             sends the client
#
# The `shiny___` prefix marks a function as reaching into shiny's namespace, and
# each reaches it with `utils::getFromNamespace()`. `.restore_input_values()`
# composes the first two into the accessor the rest of the file uses.
#
# SPIKE RESULT (shiny 1.13.0): The active restore context is reached via
# shiny's `hasCurrentRestoreContext()` (guard) and
# `getCurrentRestoreContext()`, which peeks `restoreCtxStack` and falls
# back to `getDefaultReactiveDomain()$restoreContext`. The context's `$input`
# field is a shiny `RestoreInputSet` R6 object. Its parsed input map lives in
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
shiny___to_json <- function(x) {
  # Serialize with Shiny's own wrapper so bookmark restore values go over the
  # wire exactly like every other value Shiny sends the client.
  #
  # NOTE: this does NOT escape non-ASCII. jsonlite has no `ensure_ascii`
  # equivalent, so U+2028/U+2029 still have to be escaped by the caller.
  shiny_to_json <- utils::getFromNamespace("toJSON", "shiny")
  shiny_to_json(x)
}

#' @keywords internal
shiny___has_current_restore_context <- function() {
  # TRUE when a restore context is active for the current request. Returns FALSE
  # (it does not error) outside an HTTP request and when no bookmark query
  # string was parsed.
  f <- utils::getFromNamespace("hasCurrentRestoreContext", "shiny")
  f()
}

#' @keywords internal
shiny___get_current_restore_context <- function() {
  # The active restore context. Only valid when
  # shiny___has_current_restore_context() is TRUE.
  f <- utils::getFromNamespace("getCurrentRestoreContext", "shiny")
  f()
}

#' @keywords internal
.restore_input_values <- function() {
  # Return the parsed restore input values for the current request as a named
  # list, WITHOUT marking them used (mirrors Python ctx.input.as_dict()).
  # Returns list() when there is no active restore context (e.g. outside an
  # HTTP request, or no bookmark query string was parsed).
  # `hasCurrentRestoreContext()` already returns FALSE (it does not error)
  # outside an HTTP request and when no bookmark query string was parsed, so no
  # blanket tryCatch is needed here. Errors from the shiny internals below are
  # deliberately allowed to propagate: swallowing them would silently disable
  # bookmark restore across a shiny release that changed those internals, with
  # no signal to the app author. Python narrows the same way, catching only the
  # RuntimeError raised when there is no session (#184).
  if (!shiny___has_current_restore_context()) {
    return(list())
  }
  ctx <- shiny___get_current_restore_context()
  if (is.null(ctx) || is.null(ctx$input)) {
    return(list())
  }
  values <- ctx$input$asList()
  if (is.null(values)) list() else values
}

#' @keywords internal
restore_script_tag <- function() {
  values <- .restore_input_values()
  if (length(values) == 0L) {
    return(NULL)
  }
  # Layer 1: JSON of the values, via the same serializer Shiny uses for every
  # other value it sends the client, so restored inputs serialize identically to
  # normal output values. Its defaults are what we want and jsonlite's are not:
  # `digits = I(16)` (jsonlite defaults to 4, silently rounding doubles --
  # 3.14159265 became 3.1416), `null = "null"` / `na = "null"` (jsonlite emits
  # NULL as `{}`; Python's json.dumps emits `null`), and `auto_unbox = TRUE`.
  json_payload <- as.character(shiny___to_json(values))
  # Neutralize "</" so the payload can't close the surrounding <script> tag.
  json_payload <- gsub("</", "<\\/", json_payload, fixed = TRUE)
  # Escape U+2028 / U+2029: legal in a JSON string, but JS line terminators and
  # therefore illegal inside a JS string literal. Python gets this for free from
  # `json.dumps(ensure_ascii = TRUE)`; jsonlite has no ASCII-escaping mode at
  # all (and neither does shiny's wrapper), so it must be done here (issue #183).
  json_payload <- gsub("\u2028", "\\u2028", json_payload, fixed = TRUE)
  json_payload <- gsub("\u2029", "\\u2029", json_payload, fixed = TRUE)
  # Layer 2: wrap as a JS string literal (double-encode) so quotes/newlines
  # survive the JS parser before JSON.parse runs. `unbox()` states the scalar
  # contract explicitly instead of leaning on the `auto_unbox` heuristic. This
  # layer is a plain string encode, not a Shiny value, so jsonlite directly.
  js_string_literal <- jsonlite::toJSON(jsonlite::unbox(json_payload))
  js <- paste0(
    "window.shinyreact = window.shinyreact || {};",
    "window.shinyreact._restore = JSON.parse(",
    js_string_literal,
    ");"
  )
  htmltools::tags$script(htmltools::HTML(js))
}
