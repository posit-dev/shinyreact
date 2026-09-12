.www_dir <- function() {
  system.file("lib", "shiny", package = "shinyreact")
}

# `@posit-dev/shinyreact`'s version, i.e. the release of the bundle in
# `inst/lib/shiny/`. It is the shinyreact htmlDependency's version, so
# `/lib/shinyreact-0.1.1/shinyreact.js` names the JS release being served and
# an npm-tier app can read the page source to see whether its bundled copy
# matches the server's. Bump alongside `pkg-js/package.json`; `test-dep.R`
# pins the two together. Mirrors Python's `_SHINYREACT_JS_VERSION`.
.shinyreact_js_version <- "0.1.1"

# Internal: TRUE only in a repo checkout (`load_all()`), where the repo's
# `pkg-js/package.json` sits four levels above `inst/lib/shiny/`. Never TRUE
# for an installed package.
.dev_checkout <- function() {
  file.exists(file.path(
    .www_dir(),
    "..",
    "..",
    "..",
    "..",
    "pkg-js",
    "package.json"
  ))
}

# Internal: `.shinyreact_js_version`, suffixed with the bundle's mtime in a
# dev checkout. Installed, a page loads `/lib/shinyreact-0.1.1/`; in the repo
# it loads `/lib/shinyreact-0.1.1.<mtime>/` instead, so `make update-dist`
# still cache-busts while the URL still names the release. Mirrors Python's
# `_bundle_version()`.
.bundle_version <- function() {
  if (.dev_checkout()) {
    mtime <- suppressWarnings(file.mtime(file.path(
      .www_dir(),
      "shinyreact.js"
    )))
    if (length(mtime) == 1L && !is.na(mtime)) {
      return(paste0(.shinyreact_js_version, ".", as.integer(mtime)))
    }
  }
  .shinyreact_js_version
}

# Internal: bare bundle dependency for per-output consumers.
shinyreact_dep <- function() {
  htmltools::htmlDependency(
    name = "shinyreact",
    version = .bundle_version(),
    src = c(file = .www_dir()),
    script = list(src = "shinyreact.js", defer = ""),
    stylesheet = "shinyreact.css"
  )
}

# Internal: page-level dependency = bundle + `#shinyreact-config` tag. The
# config tag carries the protocol version on every page and the bookmark
# restore payload when one is active.
#
# The tag is wrapped in `tags$head()` so it lands in `<head>`, matching Python's
# `head_content()`. Without the wrapper it renders inline in `<body>` -- the
# client finds it by id either way, but the two servers disagreed about where a
# documented `<head>` tag goes, and `page_react_html()` (via `config_head_dep()`)
# already put it in the head.
#
# `shinyreact_js = "client"` omits shinyreact.js / shinyreact.css for npm-tier
# pages, whose client bundle ships its own copy. The config tag is always
# emitted: it carries the protocol version and any bookmark restore payload.
shinyreact_dep_page <- function(shinyreact_js = "server") {
  htmltools::tagList(
    if (serves_bundle(shinyreact_js)) shinyreact_dep(),
    htmltools::tags$head(config_script_tag())
  )
}

# Internal: validate `shinyreact_js=` and say whether the page attaches the
# bundle. The one place the value is checked, so every entry point rejects a
# typo the same way. Mirrors Python's `_serves_bundle()`.
serves_bundle <- function(shinyreact_js) {
  if (
    !identical(shinyreact_js, "server") && !identical(shinyreact_js, "client")
  ) {
    cli::cli_abort(c(
      "{.arg shinyreact_js} must be {.val server} or {.val client},
       not {.val {shinyreact_js}}.",
      "i" = "{.val server} (the default) serves {.file shinyreact.js} from the
             shinyreact package -- what a no-build app needs.",
      "i" = "{.val client} is for an app whose own bundle imports
             {.pkg @posit-dev/shinyreact} and therefore ships its own copy."
    ))
  }
  identical(shinyreact_js, "server")
}

# Internal: the `#shinyreact-config` tag as an htmlDependency `head` entry, for
# UIs where a plain tag has no place to land — htmlTemplate() documents render
# attached dependencies at the dependency placeholder, and a dependency's `head`
# HTML rides along verbatim. src is an empty href: the dependency ships no
# files, only head content.
config_head_dep <- function() {
  htmltools::htmlDependency(
    name = "shinyreact-config",
    version = .protocol_version,
    src = c(href = ""),
    head = as.character(config_script_tag()),
    all_files = FALSE
  )
}
