`%||%` <- function(a, b) if (is.null(a)) b else a

test_that("shinyreact_dep() points at the bundled assets", {
  dep <- shinyreact:::shinyreact_dep()
  expect_s3_class(dep, "html_dependency")
  expect_identical(dep$name, "shinyreact")
  expect_identical(
    dep$script[["src"]] %||% dep$script[[1]]$src,
    "shinyreact.js"
  )
})

test_that("shinyreact_dep() version is a non-empty string", {
  dep <- shinyreact:::shinyreact_dep()
  expect_true(is.character(dep$version) && nzchar(dep$version))
})

test_that("shinyreact_dep_page() returns the bundle dep when no restore context", {
  out <- shinyreact:::shinyreact_dep_page()
  expect_true(
    inherits(out, "html_dependency") || inherits(out, "shiny.tag.list")
  )
})
