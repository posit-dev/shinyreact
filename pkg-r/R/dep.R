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

# Stub replaced in bookmark.R (a later task). Returns NULL when no restore context.
restore_script_tag <- function() {
  NULL
}

# Internal: page-level dependency = bundle + bookmark restore <script> (if any).
shinyreact_dep_page <- function() {
  restore <- restore_script_tag()
  if (is.null(restore)) {
    return(shinyreact_dep())
  }
  htmltools::tagList(shinyreact_dep(), restore)
}
