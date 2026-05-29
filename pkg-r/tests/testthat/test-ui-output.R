test_that("ui_output() builds a shinyreact-output div with the dep", {
  tag <- ui_output("hello")
  expect_s3_class(tag, "shiny.tag")
  expect_identical(tag$attribs$id, "hello")
  expect_identical(tag$attribs$class, "shinyreact-output")
  deps <- htmltools::findDependencies(tag)
  expect_true(any(vapply(deps, function(d) d$name == "shinyreact", logical(1))))
})

test_that("ui_output() includes extra_deps", {
  extra <- htmltools::htmlDependency("mydep", "1.0.0", src = c(href = "x"))
  tag <- ui_output("hello", extra_deps = list(extra))
  deps <- htmltools::findDependencies(tag)
  names <- vapply(deps, function(d) d$name, character(1))
  expect_true(all(c("shinyreact", "mydep") %in% names))
})
