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

test_that("shinyreact_dep_page() puts the config tag in <head>, not <body>", {
  # Python emits the tag via head_content(); R must agree on placement.
  # Mirrors Python's test_dep_page_no_context_includes_config_tag, which
  # asserts a head_content() dependency rather than an inline tag.
  rendered <- htmltools::renderTags(shinyreact:::shinyreact_dep_page())
  expect_match(as.character(rendered$head), "shinyreact-config", fixed = TRUE)
  expect_no_match(
    as.character(rendered$html),
    "shinyreact-config",
    fixed = TRUE
  )
})

test_that("page_react() puts the config tag in <head>, not <body>", {
  app_dir <- withr::local_tempdir()
  dir.create(file.path(app_dir, "www"))
  writeLines("// ui", file.path(app_dir, "www", "ui.js"))
  withr::local_dir(app_dir)

  rendered <- htmltools::renderTags(page_react())
  expect_match(as.character(rendered$head), "shinyreact-config", fixed = TRUE)
  expect_no_match(
    as.character(rendered$html),
    "shinyreact-config",
    fixed = TRUE
  )
})
