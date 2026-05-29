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
  # Sort elements by key so the root and ancestors precede their descendants
  # (pre-order depth-first).  auto_NNN keys sort lexicographically correctly
  # for up to 999 nodes.
  elements <- elements[sort(names(elements))]
  list(root = root_key, elements = elements)
}

S7::method(to_spec, S7::class_any) <- function(x) {
  x
}
