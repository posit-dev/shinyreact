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

#' Create a React page from conventional assets — no HTML file required
#'
#' The zero-configuration page for the `ui.tsx` pattern: the server emits no
#' body HTML at all. Attaches the shinyreact bundle plus your app's entry
#' assets, discovered at `www/ui.js` and `www/ui.css` (relative to the working
#' directory — the app directory under `shiny::runApp()`). Your JS owns the
#' DOM: create and append your own mount container, e.g.
#' `ReactDOM.createRoot(document.body.appendChild(document.createElement("div")))`.
#'
#' `ui.js` is required (a missing file warns, pointing at the resolved path);
#' `ui.css` is attached only when it exists. Both are served as an
#' [htmltools::htmlDependency] versioned by `ui.js`'s mtime, so the browser
#' re-fetches after every edit — unlike raw `<script src=...>` tags in a
#' hand-written HTML file, which the browser caches.
#'
#' @param ... Extra children or [htmltools::htmlDependency] objects.
#' @param src_dir Directory containing the assets. Defaults to `"www"`,
#'   relative to the working directory.
#' @param js_file JS entry filename within `src_dir`. Defaults to `"ui.js"`.
#' @param css_file CSS filename within `src_dir`. Defaults to `"ui.css"`.
#' @param title Page title. Defaults to the app folder's name (`src_dir`'s
#'   parent when `src_dir` is a `www` directory).
#' @param lang HTML `lang` attribute.
#' @return UI suitable for `shinyApp(ui = ...)`.
#' @export
page_react <- function(
  ...,
  src_dir = "www",
  js_file = "ui.js",
  css_file = "ui.css",
  title = NULL,
  lang = "en"
) {
  base_dir <-
    if (basename(src_dir) == "www") {
      dirname(normalizePath(src_dir, mustWork = FALSE))
    } else {
      normalizePath(src_dir, mustWork = FALSE)
    }
  app_name <- basename(base_dir)
  page_bare(
    shinyreact_dep_page(),
    page_react_dep(
      src_dir,
      js_file = js_file,
      css_file = css_file,
      name = app_name
    ),
    ...,
    title = if (is.null(title)) app_name else title,
    lang = lang
  )
}

#' Serve a React `index.html` document (the `ui.tsx` pattern)
#'
#' Reads a complete HTML document — the kind a Vite build emits — and injects
#' the shinyreact page-level dependencies into it via
#' [htmltools::htmlTemplate()]. The document must contain a
#' `{{ headContent() }}` marker inside `<head>`; Shiny's and shinyreact's
#' script/link tags render there. Use as the `ui` argument:
#' `shinyApp(ui = page_react_html(), server = ...)`.
#'
#' Assets the document references (your bundle's JS/CSS) should live in `www/`,
#' where Shiny serves them statically.
#'
#' For apps that don't need to own the HTML document, prefer [page_react()] —
#' it requires no HTML file at all.
#'
#' @section Path resolution:
#' A relative `path` resolves against the process working directory. Under
#' `shiny::runApp()` / `shiny::shinyApp()` that is the app directory, so the
#' default `"www/index.html"` just works. R has no per-caller `__file__`, so
#' unlike Python — which resolves a relative path against the calling module's
#' directory — there is nothing to resolve against outside the working
#' directory. Pass an absolute path if you need to be independent of it.
#'
#' @param path Path to the HTML document. Defaults to `"www/index.html"`,
#'   relative to the working directory.
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
  # brio::read_file() always reads UTF-8 and never touches line endings.
  html <- brio::read_file(path)
  if (!grepl("{{ headContent() }}", html, fixed = TRUE)) {
    cli::cli_abort(c(
      "{.path {path}} must be a complete HTML document containing a
       {.code {{{{ headContent() }}}}} marker inside {.code <head>}.",
      "i" = "shinyreact's script and stylesheet tags render at the marker.",
      "i" = "For a page without an HTML file, use {.fn page_react} instead."
    ))
  }
  ui <- htmltools::htmlTemplate(path, document_ = TRUE)
  htmltools::attachDependencies(
    ui,
    list(shinyreact_dep(), config_head_dep()),
    append = TRUE
  )
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
#' Both the script and the stylesheet are attached only when the file exists
#' inside `src_dir`, so a bundle that ships no CSS — or that has not been built
#' yet — does not emit a tag pointing at a 404. Pass `css_file = NULL` to never
#' attach a stylesheet. A missing `js_file` warns, since it is the entry point
#' and an empty dependency would otherwise fail silently.
#'
#' @param src_dir Directory containing the JS/CSS. Required; Python infers this
#'   from the calling module's `__file__` when omitted, which R has no
#'   equivalent of.
#' @param js_file JS filename within `src_dir`. Defaults to `"main.js"`,
#'   matching Python; attached only if the file exists.
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
  js_exists <- file.exists(js_path)
  mtime <- suppressWarnings(file.mtime(js_path))
  version <-
    if (length(mtime) == 1L && !is.na(mtime)) {
      as.character(as.integer(mtime))
    } else {
      "0"
    }
  if (!js_exists) {
    # An empty dependency loads nothing and reports nothing, so say so here --
    # without the tag there is not even a 404 in the console to go on.
    cli::cli_warn(c(
      "JS entry point not found: {.path {js_path}}",
      "i" = "No script tag will be emitted. Build the bundle first?"
    ))
  }
  script <- if (js_exists) list(src = js_file, type = "module") else NULL
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
    script = script,
    stylesheet = stylesheet
  )
}
