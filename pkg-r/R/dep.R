.www_dir <- function() {
  system.file("lib", "shiny", package = "shinyreact")
}

.bundle_version <- function() {
  js <- file.path(.www_dir(), "shinyreact.js")
  mtime <- suppressWarnings(file.mtime(js))
  if (length(mtime) == 1L && !is.na(mtime)) {
    return(as.character(as.integer(mtime)))
  }
  as.character(utils::packageVersion("shinyreact"))
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
shinyreact_dep_page <- function() {
  htmltools::tagList(shinyreact_dep(), config_script_tag())
}

# Internal: the `#shinyreact-config` tag as an htmlDependency `head` entry, for
# UIs where a plain tag has no place to land — htmlTemplate() documents render
# attached dependencies into `{{ headContent() }}`, and a dependency's `head`
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
