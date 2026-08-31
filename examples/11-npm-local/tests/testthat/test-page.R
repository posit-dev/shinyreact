# Pins this example's distinctive `(test)` leaf for app.R: the page ships no
# shinyreact JS. The client runtime lives entirely in www/ui.js, bundled from
# the `@posit/shinyreact` copy inside the installed shinyreact package, so the
# page must carry this app's dependency and only this app's — and no
# #shinyreact-config tag, because nothing needs a protocol handshake when one
# install owns both halves.
#
# Mirrors Python's tests/test_page.py. It rebuilds app.R's two-line ui rather
# than sourcing the app, because sourcing it would start a Shiny app.
#
# Run it from the app directory:
#
#   Rscript -e 'shiny::runTests()'

library(shinyreact)

app_ui <- function(src_dir) {
  page_bare(
    page_react_dep(src_dir, name = "npm-local"),
    title = "Old Faithful"
  )
}

test_that("the page carries only this app's dependency", {
  # The claim is about how the page is composed, not about what www/ holds, so
  # the dependency's directory need not exist here: page_react_dep() still
  # emits the (script-less) dependency and warns. That keeps the test working
  # from the app directory AND from pkg-r's suite, which sources it from
  # elsewhere.
  ui <- suppressWarnings(app_ui("www"))
  names <- vapply(htmltools::findDependencies(ui), function(d) d$name, "")

  expect_true("npm-local" %in% names)
  expect_false("shinyreact" %in% names)
})

test_that("the page has no config tag", {
  ui <- suppressWarnings(app_ui("www"))

  expect_false(grepl(
    "shinyreact-config",
    paste(as.character(htmltools::renderTags(ui)$html), collapse = "")
  ))
})
