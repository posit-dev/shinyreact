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

#' Serve a static React `index.html` (the `ui.tsx` pattern)
#'
#' Reads an HTML file and attaches the shinyreact page-level dependency. Use as
#' the `ui` argument: `shinyApp(ui = page_react_html(), server = ...)`. Works
#' with plain HTML (no `{{ headContent() }}` template syntax required).
#'
#' @section Path resolution:
#' A relative `path` resolves against the process working directory. Under
#' `shiny::runApp()` / `shiny::shinyApp()` that is the app directory, so the
#' default `"www/index.html"` just works. R has no per-caller `__file__`, so
#' unlike Python — which resolves a relative path against the calling module's
#' directory — there is nothing to resolve against outside the working
#' directory. Pass an absolute path if you need to be independent of it.
#'
#' @param path Path to the HTML file. Defaults to `"www/index.html"`, relative
#'   to the working directory.
#' @return UI suitable for `shinyApp(ui = ...)`.
#' @export
page_react_html <- function(path = "www/index.html") {
  if (!file.exists(path)) {
    cli::cli_abort(c(
      "HTML file not found: {.path {path}}",
      "i" = "Relative paths resolve against the working directory,
             {.path {getwd()}}."
    ))
  }
  # Read the bytes verbatim rather than readLines() + paste(collapse = "\n"),
  # which drops a trailing newline and rewrites CRLF -- Python's read_text() is
  # byte-exact, so the same index.html must render identically (#184).
  html <- readChar(path, file.size(path), useBytes = TRUE)
  Encoding(html) <- "UTF-8"
  htmltools::tagList(shinyreact_dep_page(), htmltools::HTML(html))
}

#' HTML dependency for a downstream package's own JS/CSS bundle
#'
#' Convenience mirroring Python's `page_react_dep()`. Versioned by the JS
#' file's mtime so browsers re-fetch after a rebuild.
#'
#' The script tag is emitted as `type="module"`. A classic
#' `<script defer>` tag throws on the bundle's first `import`. `type="module"`
#' is implicitly deferred, so no `defer` attribute is needed. If your bundle is
#' a classic (non-module) script, build an [htmltools::htmlDependency] directly
#' instead of using this helper.
#'
#' The stylesheet is attached only when `css_file` exists inside `src_dir`, so a
#' bundle that ships no CSS does not produce a 404. Pass `css_file = NULL` to
#' never attach one.
#'
#' @param src_dir Directory containing the JS/CSS. Required; Python infers this
#'   from the calling module's `__file__` when omitted, which R has no
#'   equivalent of.
#' @param js_file JS filename within `src_dir`. Defaults to `"main.js"`,
#'   matching Python.
#' @param css_file CSS filename within `src_dir`. Defaults to `"main.css"`,
#'   matching Python; attached only if the file exists. `NULL` to skip.
#' @param name Dependency name; defaults to `basename(src_dir)`.
#' @return An [htmltools::htmlDependency].
#' @export
page_react_dep <- function(
  src_dir,
  js_file = "main.js",
  css_file = "main.css",
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
  stylesheet <-
    if (!is.null(css_file) && file.exists(file.path(src_dir, css_file))) {
      css_file
    } else {
      NULL
    }
  htmltools::htmlDependency(
    name = name,
    version = version,
    src = c(file = src_dir),
    script = list(src = js_file, type = "module"),
    stylesheet = stylesheet
  )
}
