test_that("page_react emits no #root div but includes the shinyreact dep", {
  ui <- page_react()
  html <- as.character(ui)
  expect_no_match(html, 'id="root"')
  deps <- htmltools::findDependencies(ui)
  expect_true(any(vapply(deps, function(d) d$name == "shinyreact", logical(1))))
})

test_that("page_bare wraps children without #root", {
  ui <- page_bare(htmltools::div("hi"))
  html <- as.character(ui)
  expect_no_match(html, 'id="root"')
})

test_that("page_react_html reads a plain HTML file and attaches the dep", {
  tmp <- withr::local_tempfile(fileext = ".html")
  writeLines(
    "<!DOCTYPE html><html><body><div id='root'></div></body></html>",
    tmp
  )
  ui <- page_react_html(tmp)
  deps <- htmltools::findDependencies(ui)
  expect_true(any(vapply(deps, function(d) d$name == "shinyreact", logical(1))))
})

test_that("page_react_html errors clearly on a missing file", {
  expect_error(page_react_html("does-not-exist.html"), "not found")
})
