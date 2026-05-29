#' Normalize a value to the shinyreact wire shape
#'
#' Converts a [Node], [Element], or [Spec] to a plain nested list of the form
#' `list(root = <key>, elements = <named list>)`. Unclassed inputs (plain
#' lists, vectors) pass through unchanged, so any JSON-serializable value can
#' be returned from [render_reactive()].
#'
#' Downstream packages register methods on their own S7 classes:
#' `S7::method(to_spec, MyComponent) <- function(x) { ... }`.
#'
#' @param x A `Node`, `Element`, `Spec`, or any JSON-serializable value.
#' @return A plain list (wire shape) or the input unchanged.
#' @export
to_spec <- S7::new_generic("to_spec", "x")

.element_to_list <- function(el) {
  list(type = el@type, props = el@props, children = el@children)
}

S7::method(to_spec, Element) <- function(x) {
  key <- "auto_001"
  els <- list()
  els[[key]] <- .element_to_list(x)
  list(root = key, elements = els)
}

S7::method(to_spec, Spec) <- function(x) {
  els <- lapply(x@elements, .element_to_list)
  list(root = x@root, elements = els)
}

S7::method(to_spec, Node) <- function(x) {
  elements <- list()
  counter <- 0L

  walk <- function(n) {
    counter <<- counter + 1L
    key <- sprintf("auto_%03d", counter)
    child_keys <- lapply(n@children, walk)
    elements[[key]] <<- list(
      type = n@type,
      props = n@props,
      children = child_keys
    )
    key
  }

  root_key <- walk(x)
  # The counter is assigned in pre-order (root gets the lowest number before
  # its subtree is walked).  Sort by the integer suffix so the root precedes
  # its descendants regardless of node count.
  ord <- order(as.integer(sub("^auto_", "", names(elements))))
  elements <- elements[ord]
  list(root = root_key, elements = elements)
}

S7::method(to_spec, S7::class_any) <- function(x) {
  x
}

# Force a list that should serialize as a JSON object (even when empty).
# jsonlite emits an unnamed empty list as `[]`; tagging with names = character()
# makes it `{}`.
.as_json_object <- function(x) {
  if (is.list(x) && length(x) == 0L) {
    return(structure(list(), names = character()))
  }
  x
}

# Recursively mark `props` sub-lists so empty ones serialize as objects.
.mark_objects <- function(node) {
  if (!is.list(node)) {
    return(node)
  }
  if (!is.null(node$props)) {
    node$props <- .as_json_object(node$props)
  }
  if (!is.null(node$elements)) {
    node$elements <- lapply(node$elements, .mark_objects)
  }
  node
}

#' @keywords internal
.wire_json <- function(x) {
  payload <- .mark_objects(x)
  jsonlite::toJSON(
    payload,
    auto_unbox = TRUE,
    null = "null",
    na = "null"
  )
}
