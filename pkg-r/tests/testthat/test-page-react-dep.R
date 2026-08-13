test_that("page_react_dep() returns an html_dependency pointing at src_dir", {
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "main.js"))

  dep <- page_react_dep(dir, "main.js")
  expect_s3_class(dep, "html_dependency")
  expect_identical(dep$src$file, dir)
  expect_identical(dep$name, basename(dir))
})

test_that("page_react_dep() versions by the JS file's mtime", {
  dir <- withr::local_tempdir()
  js <- file.path(dir, "main.js")
  writeLines("// app", js)

  dep <- page_react_dep(dir, "main.js")
  expect_identical(dep$version, as.character(as.integer(file.mtime(js))))
})

test_that("page_react_dep() falls back to version \"0\" when the JS is missing", {
  dir <- withr::local_tempdir()
  expect_identical(page_react_dep(dir, "main.js")$version, "0")
})

test_that("page_react_dep() honours custom filenames and the name override", {
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "app.js"))
  writeLines("/* styles */", file.path(dir, "app.css"))

  dep <- page_react_dep(dir, "app.js", css_file = "app.css", name = "my-app")
  expect_identical(dep$name, "my-app")
  expect_identical(dep$script[["src"]], "app.js")
  expect_identical(dep$stylesheet, "app.css")
})

test_that("page_react_dep() defaults to main.js / main.css like Python", {
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "main.js"))
  writeLines("/* styles */", file.path(dir, "main.css"))

  dep <- page_react_dep(dir)
  expect_identical(dep$script[["src"]], "main.js")
  expect_identical(dep$stylesheet, "main.css")
})

test_that("page_react_dep() omits the stylesheet when the CSS is absent", {
  # A bundle that ships no CSS should not 404 on main.css (#184).
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "main.js"))

  expect_null(page_react_dep(dir)$stylesheet)
  expect_null(page_react_dep(dir, css_file = NULL)$stylesheet)
})

test_that("page_react_dep() emits script type=\"module\" and no defer", {
  # Matches Python (`page_react_dep()` in _page.py); an ESM bundle throws on
  # its first `import` when served from a classic <script> tag. See #182.
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "main.js"))

  dep <- page_react_dep(dir, "main.js")
  expect_identical(dep$script[["type"]], "module")
  expect_null(dep$script[["defer"]])

  html <- as.character(htmltools::renderDependencies(list(dep)))
  expect_match(html, 'type="module"', fixed = TRUE)
  expect_no_match(html, "defer", fixed = TRUE)
})
