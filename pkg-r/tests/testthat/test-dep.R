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

test_that("shinyreact_dep() emits the bundle script with defer and no type", {
  # Mirrors Python's test_dep_script_has_defer. R had no assertion on the
  # bundle's script attributes at all, which is exactly how #182 (wrong
  # attributes in R, pinned in Python) survived as long as it did.
  dep <- shinyreact:::shinyreact_dep()
  script <- if (is.null(dep$script$src)) dep$script[[1]] else dep$script
  expect_identical(script$src, "shinyreact.js")
  expect_identical(script$defer, "")
  expect_null(script$type)
})

test_that("shinyreact_dep() attaches the stylesheet unconditionally", {
  # No existence check on the CSS, unlike page_react_dep()'s. Asserted in both
  # languages so the divergence stays deliberate.
  dep <- shinyreact:::shinyreact_dep()
  expect_identical(unname(unlist(dep$stylesheet)), "shinyreact.css")
})

test_that("shinyreact_dep() versions by the JS package version", {
  # Installed, `/lib/shinyreact-<version>/` names the @posit-dev/shinyreact
  # release being served. Mirrors Python's
  # test_dep_version_is_the_js_package_version.
  local_mocked_bindings(.dev_checkout = function() FALSE)
  expect_identical(
    shinyreact:::shinyreact_dep()$version,
    shinyreact:::.shinyreact_js_version
  )
})

test_that("shinyreact_dep() version adds the bundle mtime in a dev checkout", {
  # So `make update-dist` still cache-busts during development. Mirrors
  # Python's test_dep_version_adds_bundle_mtime_in_dev_checkout.
  local_mocked_bindings(.dev_checkout = function() TRUE)
  js <- file.path(shinyreact:::.www_dir(), "shinyreact.js")
  expect_identical(
    shinyreact:::shinyreact_dep()$version,
    paste0(shinyreact:::.shinyreact_js_version, ".", as.integer(file.mtime(js)))
  )
})

test_that(".shinyreact_js_version matches pkg-js/package.json", {
  # The hardcoded version is bumped in step with the npm package. Mirrors
  # Python's test_js_version_constant_matches_package_json.
  package_json <- file.path(
    testthat::test_path(),
    "..",
    "..",
    "..",
    "pkg-js",
    "package.json"
  )
  skip_if_not(file.exists(package_json), "not running from the repo")
  expected <- jsonlite::read_json(package_json)$version
  expect_identical(shinyreact:::.shinyreact_js_version, expected)
})
