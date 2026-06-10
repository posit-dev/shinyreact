#' Bare HTML page with Shiny dependencies
#'
#' Escape hatch for custom setups. Wraps [shiny::bootstrapPage()].
#'
#' @param ... Child tags or [htmltools::htmlDependency] objects.
#' @param title Page title.
#' @param lang HTML `lang` attribute.
#' @return A `shiny.tag` page.
#' @export
page_bare <- function(..., title = NULL, lang = "en") {
  shiny::bootstrapPage(..., title = title, lang = lang)
}

#' Full-page React app served by Shiny
#'
#' Creates a page with the shinyreact page-level dependency
#' (bundle + bookmark restore script). Pass app JS/CSS dependencies (e.g. from
#' [page_react_dep()]) via `...`.
#'
#' @inheritParams page_bare
#' @return A `shiny.tag` page.
#' @export
page_react <- function(..., title = NULL, lang = "en") {
  page_bare(
    shinyreact_dep_page(),
    ...,
    title = title,
    lang = lang
  )
}

#' Serve a static React `index.html` (the `ui.tsx` pattern)
#'
#' Reads an HTML file and attaches the shinyreact page-level dependency. Use as
#' the `ui` argument: `shinyApp(ui = page_react_html(), server = ...)`. Works
#' with plain HTML (no `{{ headContent() }}` template syntax required).
#'
#' @param path Path to the HTML file. Defaults to `"www/index.html"`.
#' @return UI suitable for `shinyApp(ui = ...)`.
#' @export
page_react_html <- function(path = "www/index.html") {
  if (!file.exists(path)) {
    cli::cli_abort("HTML file not found: {.path {path}}")
  }
  html <- htmltools::HTML(paste(
    readLines(path, encoding = "UTF-8", warn = FALSE),
    collapse = "\n"
  ))
  htmltools::tagList(shinyreact_dep_page(), html)
}

#' HTML dependency for a downstream package's own JS/CSS bundle
#'
#' Convenience mirroring Python's `page_react_dep()`. Versioned by the JS
#' file's mtime so browsers re-fetch after a rebuild.
#'
#' @param src_dir Directory containing the JS/CSS.
#' @param js_file JS filename within `src_dir`.
#' @param css_file Optional CSS filename within `src_dir`.
#' @param name Dependency name; defaults to `basename(src_dir)`.
#' @return An [htmltools::htmlDependency].
#' @export
page_react_dep <- function(
  src_dir,
  js_file,
  css_file = NULL,
  name = basename(src_dir)
) {
  js_path <- file.path(src_dir, js_file)
  mtime <- suppressWarnings(file.mtime(js_path))
  version <-
    if (length(mtime) == 1L && !is.na(mtime)) {
      as.character(as.integer(mtime))
    } else {
      "0"
    }
  htmltools::htmlDependency(
    name = name,
    version = version,
    src = c(file = src_dir),
    script = list(src = js_file, defer = ""),
    stylesheet = css_file
  )
}
