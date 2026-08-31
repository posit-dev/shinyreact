# Internal: the marker a page_react_html() document must contain, where the
# rendered dependencies are inserted. Same literal as Python's
# shiny.ui.PageDocument.DEPS_PLACEHOLDER, so one document works on both servers.
deps_placeholder <- '<meta name="shiny-dependency-placeholder" content="">'

#' Bare HTML page with Shiny dependencies
#'
#' Escape hatch for custom setups. Wraps [shiny::bootstrapPage()].
#'
#' @param ... Child tags or [htmltools::htmlDependency] objects. Named
#'   arguments pass through to [shiny::bootstrapPage()] — including its own
#'   `theme`. Deliberately not surfaced as named parameters: in the `ui.tsx`
#'   pattern the client owns styling, so Bootstrap theming is a passthrough,
#'   not part of this API. Mirrors Python's `page_bare(**kwargs)`.
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
#'   parent when `src_dir` is a `www` directory), or `"shinyreact-app"` when
#'   that resolves to nothing usable (a missing `src_dir` is not an error —
#'   the bundle may not be built yet).
#' @param lang HTML `lang` attribute.
#' @param shinyreact_js Who supplies `shinyreact.js` (and `shinyreact.css`) to
#'   the page. `"server"` (the default) serves them from the shinyreact package
#'   as an [htmltools::htmlDependency] — what a no-build app needs, and what
#'   makes `window.shinyreact` exist. `"client"` is for an app whose own bundle
#'   imports `@posit/shinyreact` and therefore ships its own copy; serving them
#'   too would put two copies of React and the hooks on one page. The
#'   `#shinyreact-config` tag is emitted either way; the npm-tier client
#'   hard-errors without it. Mirrors Python's `page_react(shinyreact_js=)`.
#' @return UI suitable for `shinyApp(ui = ...)`.
#' @export
page_react <- function(
  ...,
  src_dir = "www",
  js_file = "ui.js",
  css_file = "ui.css",
  title = NULL,
  lang = "en",
  shinyreact_js = "server"
) {
  base_dir <-
    if (basename(src_dir) == "www") {
      dirname(normalizePath(src_dir, mustWork = FALSE))
    } else {
      normalizePath(src_dir, mustWork = FALSE)
    }
  app_name <- basename(base_dir)
  if (!nzchar(app_name) || app_name %in% c(".", "..")) {
    # A missing src_dir leaves normalizePath()'s path relative, so the app name
    # can come out as "." -- a nonsense title and a `/lib/.-0/` asset URL. Keep
    # the permissive resolution (the bundle may not be built yet) but name it
    # something a reader can recognize.
    app_name <- "shinyreact-app"
  }
  page_bare(
    shinyreact_dep_page(shinyreact_js = shinyreact_js),
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

# Internal: reject anything that lands in `...`.
#
# `page_react_html()`'s dots exist only to force the arguments after them to be
# named -- R's counterpart of Python's keyword-only `*`, so the same call reads
# the same in both languages. Anything that reaches `...` is either a positional
# argument the caller meant to name or a misspelled name; both deserve an error
# rather than being silently dropped.
#
# Reports names for named arguments (the misspelling case, where the name is the
# whole diagnosis) and `..1`-style positions for unnamed ones. Deliberately does
# not deparse the values: `...` is never evaluated, so a rejected argument
# cannot run someone's expensive -- or erroring -- expression on its way to
# being refused.
check_dots_empty <- function(...) {
  n <- ...length()
  if (n == 0L) {
    return(invisible(NULL))
  }
  nms <- names(match.call(expand.dots = FALSE)[["..."]])
  labels <- vapply(
    seq_len(n),
    function(i) {
      if (!is.null(nms) && nzchar(nms[[i]])) nms[[i]] else paste0("..", i)
    },
    character(1)
  )
  cli::cli_abort(
    c(
      "{.arg ...} must be empty.",
      "x" = "Unexpected argument{?s}: {.arg {labels}}.",
      "i" = "Arguments after {.arg ...} must be named, e.g.
             {.code extra_deps = } or {.code shinyreact_js = }."
    ),
    call = parent.frame()
  )
}

#' Serve a React `index.html` document (the `ui.tsx` pattern)
#'
#' Reads a complete HTML document — the kind a Vite build emits — and injects
#' the shinyreact page-level dependencies into it. The document must contain
#' Shiny's dependency placeholder inside `<head>`:
#'
#' ```html
#' <meta name="shiny-dependency-placeholder" content="">
#' ```
#'
#' Shiny's and shinyreact's script/link tags render in its place. It is an
#' ordinary `<meta>` tag rather than template syntax, so the document stays
#' valid HTML that a bundler's dev server can serve unchanged. Use as the `ui`
#' argument: `shinyApp(ui = page_react_html(), server = ...)`.
#'
#' Assets the document references (your bundle's JS/CSS) should live in `www/`,
#' where Shiny serves them statically.
#'
#' For apps that don't need to own the HTML document, prefer [page_react()] —
#' it requires no HTML file at all.
#'
#' @section The whole document is a template:
#' R places the dependencies with [htmltools::htmlTemplate()], which evaluates
#' **every** `{{ ... }}` in the document as R code — anywhere in it, `<head>` or
#' `<body>`, with the global environment as parent. So a body containing
#' `{{ 6*7 }}` renders `42`, and `{{ nonexistent() }}` is an error at page
#' render.
#'
#' A document written for a JS templating engine that also uses `{{ }}`
#' (Handlebars, Mustache, Vue's text interpolation) is therefore not safe to
#' pass here as is — those braces will be evaluated as R. Escape them, or use
#' [page_react()], which needs no HTML file at all.
#'
#' Python's `page_react_html()` differs: it replaces the placeholder and leaves
#' the rest of the document untouched. Documented as a deliberate divergence
#' rather than a bug — see `FEATURES.md` and issue #223.
#'
#' @section Path resolution:
#' A relative `path` resolves against the process working directory. Under
#' `shiny::runApp()` / `shiny::shinyApp()` that is the app directory, so the
#' default `"www/index.html"` just works. R has no per-caller `__file__`, so
#' unlike Python — which resolves a relative path against the calling module's
#' directory — there is nothing to resolve against outside the working
#' directory. Pass an absolute path if you need to be independent of it.
#'
#' The placeholder must be spelled exactly as above — the check is a
#' fixed-string match, so a differently-quoted or reordered `<meta>` tag is
#' rejected.
#'
#' @param path Path to the HTML document. Defaults to `"www/index.html"`,
#'   relative to the working directory.
#' @param ... These dots are for future extension and must be empty. They force
#'   every argument after them to be named, matching Python, where the same
#'   arguments are keyword-only. Passing anything here is an error naming what
#'   it received.
#' @param extra_deps A list of additional [htmltools::htmlDependency] objects to
#'   render at the placeholder. A complete document has no tag tree to attach
#'   dependencies to, so this is the only way in — the counterpart of
#'   [page_react()]'s `...`. They render *after* Shiny's and shinyreact's, so
#'   they can rely on `window.shinyreact` existing. Mirrors Python's
#'   `page_react_html(extra_deps=)`.
#' @param shinyreact_js Who supplies `shinyreact.js` / `shinyreact.css`:
#'   `"server"` (the default) or `"client"` for an npm-tier app whose bundle
#'   imports `@posit/shinyreact` — see [page_react()].
#' @return UI suitable for `shinyApp(ui = ...)`.
#' @export
page_react_html <- function(
  path = "www/index.html",
  ...,
  extra_deps = NULL,
  shinyreact_js = "server"
) {
  check_dots_empty(...)
  if (!file.exists(path)) {
    cli::cli_abort(c(
      "HTML file not found: {.path {path}}",
      "i" = "Relative paths resolve against the working directory,
             {.path {getwd()}}."
    ))
  }
  # brio::read_file() always reads UTF-8 and never touches line endings.
  html <- brio::read_file(path)
  if (!grepl(deps_placeholder, html, fixed = TRUE)) {
    cli::cli_abort(c(
      "{.path {path}} must be a complete HTML document containing
       {.code {deps_placeholder}} inside {.code <head>}.",
      "i" = "Shiny's and shinyreact's script and stylesheet tags render there.",
      "i" = "For a page without an HTML file, use {.fn page_react} instead."
    ))
  }
  # `htmlTemplate()` is how R places rendered dependencies, and it only knows
  # `headContent()`. Swapping the placeholder for it here keeps the *document*
  # free of template syntax, matching Python's placeholder.
  html <- sub(deps_placeholder, "{{ headContent() }}", html, fixed = TRUE)
  ui <- htmltools::htmlTemplate(text_ = html, document_ = TRUE)
  htmltools::attachDependencies(
    ui,
    c(
      if (serves_bundle(shinyreact_js)) list(shinyreact_dep()),
      list(config_head_dep()),
      extra_deps
    ),
    append = TRUE
  )
}

#' HTML dependency for a downstream package's own JS/CSS bundle
#'
#' Convenience mirroring Python's `page_react_dep()`. It is versioned by the JS
#' file's mtime, so the `/lib/{name}-{version}/` URL changes on every rebuild and
#' the browser re-fetches. That is what you want while developing and the wrong
#' thing for a published package — an mtime is whatever the install happened to
#' write, so it is neither stable across machines nor meaningful to a reader.
#' There is no `version` argument on purpose: a package shipping a fixed version
#' should build its own [htmltools::htmlDependency] (the same advice as for a
#' classic, non-module bundle), which is five lines and leaves nothing about the
#' dependency implicit.
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
#' @param js_file JS filename within `src_dir`. Defaults to `"ui.js"`,
#'   matching Python; attached only if the file exists.
#' @param css_file CSS filename within `src_dir`. Defaults to `"ui.css"`,
#'   matching Python; attached only if the file exists. `NULL` to skip.
#' @param name Dependency name; defaults to `basename(src_dir)`.
#' @return An [htmltools::htmlDependency].
#' @export
page_react_dep <- function(
  src_dir,
  js_file = "ui.js",
  css_file = "ui.css",
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
