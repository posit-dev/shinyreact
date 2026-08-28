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

full_doc <- function(body = "<div id='root'></div>", title = "T") {
  paste0(
    "<!DOCTYPE html><html><head><title>",
    title,
    "</title>",
    "{{ headContent() }}</head><body>",
    body,
    "</body></html>"
  )
}

write_full_doc <- function(path, ...) {
  writeLines(full_doc(...), path)
}

test_that("page_react_html renders shinyreact deps into the template head", {
  tmp <- withr::local_tempfile(fileext = ".html")
  write_full_doc(tmp)
  html <- render_document(page_react_html(tmp))
  expect_match(html, "shinyreact.js", fixed = TRUE)
  expect_match(html, 'id="shinyreact-config"', fixed = TRUE)
  # The user's document is the only <html> -- no nested document.
  expect_identical(
    lengths(regmatches(html, gregexpr("<html", html, fixed = TRUE))),
    1L
  )
  expect_match(html, "<title>T</title>", fixed = TRUE)
})

test_that("page_react_html emits the config payload readable by the client", {
  tmp <- withr::local_tempfile(fileext = ".html")
  write_full_doc(tmp)
  html <- render_document(page_react_html(tmp))
  config <- extract_config(html)
  expect_identical(config$protocolVersion, .protocol_version)
})

test_that("page_react_html preserves the document body", {
  tmp <- withr::local_tempfile(fileext = ".html")
  write_full_doc(tmp, body = "<main class='xyz'>content</main>")
  html <- render_document(page_react_html(tmp))
  expect_match(html, "<main class='xyz'>content</main>", fixed = TRUE)
})

test_that("page_react_html errors on a document without the marker", {
  tmp <- withr::local_tempfile(fileext = ".html")
  writeLines(
    "<!DOCTYPE html><html><head></head><body>hi</body></html>",
    tmp
  )
  expect_error(page_react_html(tmp), "headContent")
  expect_error(page_react_html(tmp), "page_react")
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
  write_full_doc(file.path(dir, "www", "index.html"), body = "<b>hi</b>")
  withr::local_dir(dir)

  html <- render_document(page_react_html())
  expect_match(html, "<b>hi</b>", fixed = TRUE)
})

local_react_app <- function(css = TRUE, env = parent.frame()) {
  # An app folder with the page_react() conventional assets, as the working
  # directory. Mirrors Python's _make_react_app().
  dir <- withr::local_tempdir("reactapp", .local_envir = env)
  dir.create(file.path(dir, "www"))
  writeLines("// ui entry", file.path(dir, "www", "ui.js"))
  if (css) {
    writeLines("body {}", file.path(dir, "www", "ui.css"))
  }
  withr::local_dir(dir, .local_envir = env)
  dir
}

dep_tags_html <- function(ui) {
  rendered <- htmltools::renderTags(ui)
  paste0(
    paste(
      vapply(
        htmltools::resolveDependencies(rendered$dependencies),
        function(d) as.character(htmltools::renderDependencies(list(d))),
        character(1)
      ),
      collapse = ""
    ),
    as.character(rendered$head),
    as.character(rendered$html)
  )
}

test_that("page_react attaches bundle, app dep, and config", {
  dir <- local_react_app()
  ui <- page_react()
  deps <- htmltools::findDependencies(ui)
  names <- vapply(deps, function(d) d$name, character(1))
  expect_true("shinyreact" %in% names)
  expect_true(basename(dir) %in% names)
  html <- dep_tags_html(ui)
  expect_match(html, "ui.js", fixed = TRUE)
  expect_match(html, "ui.css", fixed = TRUE)
  expect_match(html, 'id="shinyreact-config"', fixed = TRUE)
})

test_that("page_react title defaults to the app folder name", {
  # Mirrors Python's test_page_react_title_defaults_to_app_folder_name.
  dir <- local_react_app()
  rendered <- htmltools::renderTags(page_react())
  html <- paste0(as.character(rendered$head), as.character(rendered$html))
  expect_identical(
    regmatches(html, gregexpr("<title>.*?</title>", html))[[1]],
    paste0("<title>", basename(dir), "</title>")
  )
})

test_that("page_react title can be overridden", {
  local_react_app()
  rendered <- htmltools::renderTags(page_react(title = "Custom"))
  html <- paste0(as.character(rendered$head), as.character(rendered$html))
  expect_match(html, "<title>Custom</title>", fixed = TRUE)
})

test_that("page_react skips a missing ui.css", {
  local_react_app(css = FALSE)
  html <- dep_tags_html(page_react())
  expect_match(html, "ui.js", fixed = TRUE)
  expect_no_match(html, "ui.css", fixed = TRUE)
})

test_that("page_react warns on a missing ui.js", {
  dir <- withr::local_tempdir("emptyapp")
  dir.create(file.path(dir, "www"))
  withr::local_dir(dir)
  expect_warning(page_react(), "ui.js")
})

test_that("page_react never names the app '.' when src_dir is missing", {
  # A missing src_dir used to yield a "." title and a "/lib/.-0/" asset URL
  # (#242).
  withr::local_dir(withr::local_tempdir("nowww"))
  ui <- suppressWarnings(page_react())
  rendered <- htmltools::renderTags(ui)
  html <- paste0(as.character(rendered$head), as.character(rendered$html))
  dep_names <- vapply(
    htmltools::findDependencies(ui),
    function(d) d$name,
    character(1)
  )
  expect_no_match(html, "<title>.</title>", fixed = TRUE)
  expect_false("." %in% dep_names)

  # On Windows, normalizePath() resolves a nonexistent relative path against
  # the working directory, so the name comes out as the app folder's and the
  # fallback is unreachable.
  skip_on_os("windows")
  expect_match(html, "<title>shinyreact-app</title>", fixed = TRUE)
  expect_true("shinyreact-app" %in% dep_names)
})

test_that("page_react includes extra HTMLDependency arguments", {
  local_react_app()
  dep <- htmltools::htmlDependency(
    "extra-dep",
    "1.0",
    src = c(href = "/x"),
    script = "x.js"
  )
  deps <- htmltools::findDependencies(page_react(dep))
  expect_true(any(vapply(
    deps,
    function(d) d$name == "extra-dep",
    logical(1)
  )))
})

test_that("page_react() emits no body HTML of its own", {
  # The client appends its own mount container; the server contributes nothing
  # to <body>. Mirrors Python's test_page_react_attaches_bundle_app_dep_and_config.
  app_dir <- withr::local_tempdir()
  dir.create(file.path(app_dir, "www"))
  writeLines("// ui", file.path(app_dir, "www", "ui.js"))
  withr::local_dir(app_dir)

  body <- as.character(htmltools::renderTags(page_react())$html)
  expect_false(grepl("<div", body, fixed = TRUE))
  expect_false(grepl("root", body, fixed = TRUE))
})

test_that("page_bare() emits no #shinyreact-config tag", {
  # page_bare() is the escape hatch: Shiny's deps only, so no protocol tag.
  rendered <- htmltools::renderTags(page_bare())
  expect_no_match(
    paste(as.character(rendered$head), as.character(rendered$html)),
    "shinyreact-config",
    fixed = TRUE
  )
})

test_that("page_react_html() evaluates every {{ }} in the document (#223)", {
  # Documented, deliberate: htmlTemplate() is a whole-document template, so
  # braces in the BODY are R code too. Python replaces only the marker. This
  # pins the divergence rather than asserting it is desirable.
  dir <- withr::local_tempdir()
  dir.create(file.path(dir, "www"))
  writeLines(
    c(
      "<html><head>{{ headContent() }}</head>",
      "<body><p>{{ 6*7 }}</p></body></html>"
    ),
    file.path(dir, "www", "index.html")
  )
  withr::local_dir(dir)

  body <- as.character(htmltools::renderTags(page_react_html())$html)
  expect_match(body, "<p>42</p>", fixed = TRUE)
})

test_that("page_react_html() rejects a marker without the exact spacing", {
  # The check is a fixed-string match, so htmlTemplate()'s own tolerance for
  # {{headContent()}} does not apply. Documented in ?page_react_html.
  dir <- withr::local_tempdir()
  dir.create(file.path(dir, "www"))
  writeLines(
    "<html><head>{{headContent()}}</head><body></body></html>",
    file.path(dir, "www", "index.html")
  )
  withr::local_dir(dir)

  expect_error(page_react_html(), "headContent")
})

test_that("the exported API surface is exactly this", {
  # Pins the export set so an accidental addition or removal is a test
  # failure. Mirrors Python's test_public_api_surface_is_exactly_this.
  expect_identical(
    sort(getNamespaceExports("shinyreact")),
    sort(c(
      "page_bare",
      "page_react",
      "page_react_dep",
      "page_react_html",
      "reactive_output",
      "send_message"
    ))
  )
})

test_that("send_message() returns invisibly", {
  session <- list(
    ns = function(id) id,
    sendCustomMessage = function(type, message) invisible(NULL)
  )
  expect_invisible(send_message(session, "id", list(a = 1)))
})
