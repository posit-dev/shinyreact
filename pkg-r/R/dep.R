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
