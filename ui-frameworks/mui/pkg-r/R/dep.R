# Material UI HTML dependency.

#' HTML dependency for the MUI JS bundle
#'
#' Provides the built shinymui assets as an [htmltools::htmlDependency]. Pass it
#' to [shinyreact::output_react()] via `extra_deps`. MUI styles itself at runtime
#' via emotion, so there is no separate CSS file.
#'
#' @param www_dir Optional path to a directory containing `mui.js`. Defaults to
#'   the asset bundled in the installed package
#'   (`system.file("www", package = "shinymui")`).
#' @return An [htmltools::htmlDependency].
#' @export
mui_dep <- function(www_dir = NULL) {
  if (is.null(www_dir)) {
    www_dir <- system.file("www", package = "shinymui")
    if (!nzchar(www_dir)) {
      stop(
        "Could not locate the bundled www/ assets. Install shinymui, ",
        "load it with pkgload::load_all(), or pass `www_dir` explicitly.",
        call. = FALSE
      )
    }
  }
  www_dir <- normalizePath(www_dir, mustWork = TRUE)
  js <- file.path(www_dir, "mui.js")
  ver <- if (file.exists(js)) as.character(as.integer(file.info(js)$mtime)) else "0"
  htmltools::htmlDependency(
    name = "shinymui",
    version = ver,
    src = c(file = www_dir),
    script = list(src = "mui.js", defer = "")
  )
}
