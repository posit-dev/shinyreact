# shadcn HTML dependency.

#' HTML dependency for the shadcn JS + CSS bundle
#'
#' Provides the built shinyshadcn assets as an [htmltools::htmlDependency].
#' Pass it to [shinyreact::output_react()] via `extra_deps`.
#'
#' @param www_dir Optional path to a directory containing `shadcn.js` and
#'   `style.css`. Defaults to the assets bundled in the installed package
#'   (`system.file("www", package = "shinyshadcn")`).
#' @return An [htmltools::htmlDependency].
#' @export
shadcn_dep <- function(www_dir = NULL) {
  if (is.null(www_dir)) {
    www_dir <- system.file("www", package = "shinyshadcn")
    if (!nzchar(www_dir)) {
      stop(
        "Could not locate the bundled www/ assets. Install shinyshadcn, ",
        "load it with pkgload::load_all(), or pass `www_dir` explicitly.",
        call. = FALSE
      )
    }
  }
  www_dir <- normalizePath(www_dir, mustWork = TRUE)
  js <- file.path(www_dir, "shadcn.js")
  ver <- if (file.exists(js)) as.character(as.integer(file.info(js)$mtime)) else "0"
  htmltools::htmlDependency(
    name = "shinyshadcn",
    version = ver,
    src = c(file = www_dir),
    script = list(src = "shadcn.js", defer = ""),
    stylesheet = "style.css"
  )
}
