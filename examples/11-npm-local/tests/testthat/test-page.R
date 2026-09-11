# Pins this example's distinctive `(test)` leaf for app.R: the page ships no
# shinyreact JS. The client runtime lives entirely in www/ui.js, bundled from
# `@posit-dev/shinyreact`, so the page must carry this app's dependency and
# only this app's — and no #shinyreact-config tag, which page_bare() is alone
# in never emitting.
#
# Mirrors Python's tests/test_page.py. It rebuilds app.R's two-line ui rather
# than sourcing the app, because sourcing it would start a Shiny app.
#
# Run it from the app directory:
#
#   Rscript -e 'shiny::runTests()'

library(shinyreact)

# The claim under test is how the page is composed, not what www/ holds, so the
# ui is built against an empty asset directory in tempdir(). That keeps the
# test working from the app directory AND from pkg-r's suite, which sources it
# with a different working directory. page_react_dep() requires the directory
# to exist (#290) but only warns about the missing ui.js inside it.
app_ui <- function() {
  dir <- file.path(tempdir(), "npm-local-page-test")
  dir.create(file.path(dir, "www"), recursive = TRUE, showWarnings = FALSE)
  old <- setwd(dir)
  on.exit(setwd(old), add = TRUE)

  suppressWarnings(page_bare(
    page_react_dep("www", name = "npm-local"),
    title = "Old Faithful"
  ))
}

test_that("the page carries only this app's dependency", {
  ui <- app_ui()
  names <- vapply(htmltools::findDependencies(ui), function(d) d$name, "")

  expect_true("npm-local" %in% names)
  expect_false("shinyreact" %in% names)
})

test_that("the page has no config tag", {
  ui <- app_ui()

  expect_false(grepl(
    "shinyreact-config",
    paste(as.character(htmltools::renderTags(ui)$html), collapse = "")
  ))
})
