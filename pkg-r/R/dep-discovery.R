# Automatic renderer HTML-dependency discovery (#146, #203).
#
# R's `page_react_html()` is a plain UI value: it is rendered before any
# session's `server()` runs, so — unlike Python's Express-mode
# `set_react_page()` — output dependencies cannot be inlined into the initial
# page. Instead, after every reactive flush we diff the session's registered
# outputs, extract each new output's UI via `output_ui()`, and push any
# not-yet-sent dependencies to the client as a `shinyreact-deps` custom
# message. The JS bundle loads them and re-runs `Shiny.bindAll()`; the shiny
# client replays stored output values on late bind, and hidden-output
# suspension means most values are only computed after the bind anyway.
#
# Diffing on *every* flush (not just the first) also covers outputs registered
# after startup — e.g. a module server mounted inside an observer.
#
# The hook: the JS bundle sends one `.shinyreact_init` ping (type
# `shinyreact.init`) after Shiny initializes; that type's dedicated input
# handler (input-handler.R) calls `install_dep_discovery()`. Every session
# gets exactly one ping, whether or not the app has any other inputs.

install_dep_discovery <- function(session) {
  if (is.null(session)) {
    return(invisible(FALSE))
  }
  user_data <- tryCatch(session$userData, error = function(e) NULL)
  if (!is.environment(user_data)) {
    return(invisible(FALSE))
  }
  if (isTRUE(user_data[[".shinyreact_dep_discovery"]])) {
    return(invisible(FALSE))
  }
  # `.outputs` is private; shiny exposes no API to enumerate registered
  # outputs (Python reads `session.output._outputs`, same deal). getOutput()
  # is public. MockShinySession has neither -- discovery no-ops there.
  private <- tryCatch(session$.__enclos_env__$private, error = function(e) NULL)
  if (
    is.null(private) ||
      !is.function(session$onFlushed) ||
      !is.function(session$getOutput)
  ) {
    return(invisible(FALSE))
  }
  user_data[[".shinyreact_dep_discovery"]] <- TRUE

  seen_outputs <- character()
  sent_deps <- character()
  push_new_output_deps <- function() {
    output_names <- names(private$.outputs)
    new_names <- setdiff(output_names, seen_outputs)
    if (length(new_names) == 0L) {
      return(invisible())
    }
    seen_outputs <<- c(seen_outputs, new_names)

    deps <- list()
    for (name in new_names) {
      ui <- output_ui_or_null(session$getOutput(name), name)
      if (!is.null(ui)) {
        deps <- c(deps, htmltools::findDependencies(ui))
      }
    }
    deps <- htmltools::resolveDependencies(deps)
    keys <- vapply(
      deps,
      function(dep) paste0(dep$name, "@", dep$version),
      character(1)
    )
    deps <- deps[!(keys %in% sent_deps)]
    if (length(deps) == 0L) {
      return(invisible())
    }
    sent_deps <<- c(sent_deps, setdiff(keys, sent_deps))

    # createWebDependency() registers each dep's resource path with shiny so
    # the client can fetch the files; the client skips deps already on the
    # page by name, so overlap with the static <head> is harmless.
    session$sendCustomMessage(
      "shinyreact-deps",
      lapply(deps, shiny::createWebDependency)
    )
  }
  session$onFlushed(push_new_output_deps, once = FALSE)
  invisible(TRUE)
}
