# These tests deliberately do NOT mock `.restore_input_values()`. They drive a
# real `shiny:::RestoreContext` so the fragile part -- the
# `hasCurrentRestoreContext()` / `getCurrentRestoreContext()` /
# `RestoreInputSet$asList()` path pinned to shiny >= 1.13.0 internals -- is
# actually exercised. A shiny release that changes those internals should fail
# here rather than silently disabling bookmark restore (#185).

with_restore_values <- function(values, code) {
  ctx <- shiny:::RestoreContext$new()
  ctx$active <- TRUE
  ctx$input <- shiny:::RestoreInputSet$new(values)
  shiny:::withRestoreContext(ctx, code)
}

test_that(".restore_input_values() returns list() with no active context", {
  expect_false(shiny:::hasCurrentRestoreContext())
  expect_identical(.restore_input_values(), list())
})

test_that(".restore_input_values() reads a real restore context", {
  values <- with_restore_values(
    list(name = "Alice", n = 3L),
    .restore_input_values()
  )
  expect_setequal(names(values), c("name", "n"))
  expect_identical(values$name, "Alice")
  expect_identical(values$n, 3L)
})

test_that(".restore_input_values() does not mark values used", {
  # Mirrors Python's test_read_restore_input_values_does_not_mark_pending.
  # `RestoreInputSet$get()` appends to private$pending, which would break the
  # app's own restoreInput() calls in the same render; asList() must not.
  ctx <- shiny:::RestoreContext$new()
  ctx$active <- TRUE
  ctx$input <- shiny:::RestoreInputSet$new(list(name = "Alice"))
  shiny:::withRestoreContext(ctx, .restore_input_values())
  expect_identical(ctx$input$.__enclos_env__$private$pending, character(0))
  expect_false(ctx$input$isUsed("name"))
})

test_that(".restore_input_values() returns list() for an empty context", {
  expect_identical(with_restore_values(list(), .restore_input_values()), list())
})

test_that("restore_script_tag() emits the payload from a real context", {
  html <- with_restore_values(
    list(name = "Alice"),
    as.character(restore_script_tag())
  )
  expect_match(html, "window\\.shinyreact\\._restore = JSON\\.parse\\(")
  expect_match(html, "Alice")
})

test_that("shinyreact_dep_page() wraps in a tagList only with restore values", {
  # No context: the bare dependency. With values: dep + <script>.
  expect_s3_class(shinyreact_dep_page(), "html_dependency")
  out <- with_restore_values(list(name = "Alice"), shinyreact_dep_page())
  expect_s3_class(out, "shiny.tag.list")
  expect_match(as.character(out), "_restore")
})

test_that("page_react_html() emits the restore script when a bookmark is active", {
  # End-to-end through the exported entry point, mirroring Python's
  # test_page_react_html_emits_restore_script_when_bookmark_active.
  dir <- withr::local_tempdir()
  index <- file.path(dir, "index.html")
  writeLines(
    "<!DOCTYPE html><html><body><div id='root'></div></body></html>",
    index
  )

  html <- with_restore_values(
    list(name = "Alice"),
    as.character(htmltools::renderTags(page_react_html(index))$html)
  )
  expect_match(html, "window\\.shinyreact\\._restore")
  expect_match(html, "Alice")
})

test_that("page_react_html() emits no restore script without a bookmark", {
  dir <- withr::local_tempdir()
  index <- file.path(dir, "index.html")
  writeLines(
    "<!DOCTYPE html><html><body><div id='root'></div></body></html>",
    index
  )

  html <- as.character(htmltools::renderTags(page_react_html(index))$html)
  expect_no_match(html, "_restore", fixed = TRUE)
})
