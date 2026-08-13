test_that("page_bare wraps children without #root", {
  ui <- page_bare(htmltools::div("hi"))
  html <- as.character(ui)
  expect_no_match(html, 'id="root"')
})

test_that("page_bare renders the title exactly once", {
  # Mirrors Python's test_page_bare_title_emitted_once (#186): shiny's
  # bootstrapPage() owns <title>, so nothing else may inject one.
  rendered <- htmltools::renderTags(page_bare(title = "My Title"))
  html <- paste0(as.character(rendered$head), as.character(rendered$html))
  titles <- regmatches(html, gregexpr("<title>.*?</title>", html))[[1]]
  expect_identical(titles, "<title>My Title</title>")
})

test_that("page_bare attaches no shinyreact dependency", {
  # It is the escape hatch for setups that do not want the bundle.
  deps <- htmltools::findDependencies(page_bare(htmltools::div("hi")))
  expect_false(any(vapply(
    deps,
    function(d) d$name == "shinyreact",
    logical(1)
  )))
})

test_that("page_bare includes HTMLDependency arguments", {
  dep <- htmltools::htmlDependency(
    "my-dep",
    "1.0",
    src = c(href = "/x"),
    script = "x.js"
  )
  deps <- htmltools::findDependencies(page_bare(dep, htmltools::div("hi")))
  expect_true(any(vapply(deps, function(d) d$name == "my-dep", logical(1))))
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

test_that("page_react_html includes the HTML verbatim", {
  # Byte-exact, including the trailing newline and any CRLF -- readLines() +
  # paste(collapse = "\n") used to normalize both (#184).
  tmp <- withr::local_tempfile(fileext = ".html")
  body <- "<!DOCTYPE html>\r\n<html><body><div id='root'></div></body></html>\n"
  writeBin(charToRaw(body), tmp)

  html <- as.character(htmltools::renderTags(page_react_html(tmp))$html)
  expect_true(grepl(body, html, fixed = TRUE))
})

test_that("page_react_html errors clearly on a missing file", {
  expect_error(page_react_html("does-not-exist.html"), "not found")
})

test_that("page_react_html's not-found error names the working directory", {
  # A relative path resolves against the working directory, so saying which one
  # turns a mysterious failure into a diagnosable one (#184).
  dir <- withr::local_tempdir()
  withr::local_dir(dir)
  expect_error(page_react_html("www/index.html"), basename(dir), fixed = TRUE)
})

test_that("page_react_html resolves a relative path against the working directory", {
  dir <- withr::local_tempdir()
  dir.create(file.path(dir, "www"))
  writeLines(
    "<html><body>hi</body></html>",
    file.path(dir, "www", "index.html")
  )
  withr::local_dir(dir)

  html <- as.character(htmltools::renderTags(page_react_html())$html)
  expect_match(html, "<body>hi</body>", fixed = TRUE)
})
