test_that("page_react_dep() returns an html_dependency pointing at src_dir", {
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "ui.js"))

  dep <- page_react_dep(dir, "ui.js")
  expect_s3_class(dep, "html_dependency")
  expect_identical(dep$src$file, dir)
  expect_identical(dep$name, basename(dir))
})

test_that("page_react_dep() versions by the JS file's mtime", {
  dir <- withr::local_tempdir()
  js <- file.path(dir, "ui.js")
  writeLines("// app", js)

  dep <- page_react_dep(dir, "ui.js")
  expect_identical(dep$version, as.character(as.integer(file.mtime(js))))
})

test_that("page_react_dep() falls back to version \"0\" when the JS is missing", {
  dir <- withr::local_tempdir()
  expect_warning(dep <- page_react_dep(dir, "ui.js"), "JS entry point")
  expect_identical(dep$version, "0")
})

test_that("page_react_dep() errors when src_dir does not exist", {
  # Mirrors Python's test_page_react_dep_missing_src_dir_raises. R used to
  # build the app happily and 404 every asset at runtime; Python got
  # Starlette's "Directory '...' does not exist" from inside App(). Both now
  # fail here, where the message can name the fix.
  missing <- file.path(withr::local_tempdir(), "not-built")

  expect_error(page_react_dep(missing), "React asset directory not found")
})

test_that("page_react_dep()'s missing-src_dir error names the path and the fix", {
  missing <- file.path(withr::local_tempdir(), "not-built")

  err <- expect_error(page_react_dep(missing))
  message <- cli::ansi_strip(paste(
    conditionMessage(err),
    paste(err$body, collapse = " ")
  ))
  expect_match(message, "not-built", fixed = TRUE)
  expect_match(message, "Build the bundle first", fixed = TRUE)
  expect_match(message, "src_dir", fixed = TRUE)
})

test_that("page_react_dep() errors on src_dir before warning about js_file", {
  # No directory means no ui.js either. Warning about the file would send the
  # reader looking inside a directory that isn't there.
  missing <- file.path(withr::local_tempdir(), "not-built")

  expect_no_warning(expect_error(page_react_dep(missing)))
})

test_that("page_react_dep() rejects a file passed as src_dir", {
  # dir.exists(), not file.exists() -- a file is just as unservable.
  dir <- withr::local_tempdir()
  js <- file.path(dir, "ui.js")
  writeLines("// app", js)

  expect_error(page_react_dep(js), "React asset directory not found")
})

test_that("page_react_dep() omits the script when the JS is absent", {
  # No tag pointing at a 404 -- but warn, since an empty dependency loads
  # nothing and would otherwise fail completely silently (#184).
  dir <- withr::local_tempdir()
  expect_warning(dep <- page_react_dep(dir), "JS entry point not found")
  expect_null(dep$script)
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

test_that("page_react_dep() defaults to ui.js / ui.css like Python", {
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "ui.js"))
  writeLines("/* styles */", file.path(dir, "ui.css"))

  dep <- page_react_dep(dir)
  expect_identical(dep$script[["src"]], "ui.js")
  expect_identical(dep$stylesheet, "ui.css")
})

test_that("page_react_dep() omits the stylesheet when the CSS is absent", {
  # A bundle that ships no CSS should not 404 on ui.css (#184).
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "ui.js"))

  expect_null(page_react_dep(dir)$stylesheet)
  expect_null(page_react_dep(dir, css_file = NULL)$stylesheet)
})

test_that("page_react_dep() emits script type=\"module\" and no defer", {
  # Matches Python (`page_react_dep()` in _page.py); an ESM bundle throws on
  # its first `import` when served from a classic <script> tag. See #182.
  dir <- withr::local_tempdir()
  writeLines("// app", file.path(dir, "ui.js"))

  dep <- page_react_dep(dir, "ui.js")
  expect_identical(dep$script[["type"]], "module")
  expect_null(dep$script[["defer"]])

  html <- as.character(htmltools::renderDependencies(list(dep)))
  expect_match(html, 'type="module"', fixed = TRUE)
  expect_no_match(html, "defer", fixed = TRUE)
})
