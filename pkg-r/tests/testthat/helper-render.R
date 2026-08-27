# Render a template-mode UI (page_react_html()) to a full HTML document.
#
# htmltools::renderDocument() renders dependencies href-based, but
# shinyreact_dep() is file-based; in a running app shiny converts it via
# shiny::createWebDependency() at serve time. Mimic that conversion here so
# tests exercise the same rendering path without a live app.
render_document <- function(ui) {
  htmltools::renderDocument(
    ui,
    processDep = function(dep) {
      if (is.null(dep$src$href)) {
        dep$src <- list(href = paste0("lib/", dep$name, "-", dep$version))
      }
      dep
    }
  )
}
