# Parse the JSON payload of the `#shinyreact-config` script tag, mirroring
# `_extract_config()` / `_extract_restore_payload()` in
# pkg-py/tests/test_bookmark_restore.py. This is what the JS client does:
# locate the tag by id and JSON.parse its text content.
extract_config <- function(html) {
  # Tags go through renderTags so `tags$head()` content is picked up: the
  # config tag is hoisted to `<head>`, and `as.character()` alone returns only
  # the body HTML. Plain character input passes through untouched.
  if (inherits(html, c("shiny.tag", "shiny.tag.list"))) {
    rendered <- htmltools::renderTags(html)
    html <- c(rendered$head, rendered$html)
  }
  html <- paste(as.character(html), collapse = "\n")
  m <- regmatches(
    html,
    regexec(
      '<script[^>]*id="shinyreact-config"[^>]*>(.*?)</script>',
      html,
      perl = TRUE
    )
  )[[1]]
  expect_length(m, 2L)
  jsonlite::fromJSON(m[[2]], simplifyVector = FALSE)
}

extract_restore_payload <- function(html) {
  config <- extract_config(html)
  expect_true("restore" %in% names(config))
  config$restore
}
