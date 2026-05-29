#' Component tree data model
#'
#' `element()`, `spec()`, and `node()` construct the data sent to the browser.
#' `Element`/`Spec` are the flat wire model; `Node` is the nested authoring
#' model that flattens to a `Spec` via [to_spec()].
#'
#' @param type Component type string (e.g. `"Card"`). Single non-empty string.
#' @param props Named list of props. May be empty.
#' @param children For `element()`, a list of length-1 character element keys.
#'   For `node()`, passed via `...` and must be `Node` objects.
#' @param root For `spec()`, the key in `elements` to render first.
#' @param elements For `spec()`, a named list of `Element` objects.
#' @param ... For `node()`, child `Node` objects.
#'
#' @return An S7 object of class `Element`, `Spec`, or `Node`.
#' @name data-model
NULL

.check_type <- function(type) {
  if (!is.character(type) || length(type) != 1L) {
    return("@type must be a single string")
  }
  if (is.na(type) || !nzchar(type)) {
    return("@type must be a non-empty string")
  }
  NULL
}

.check_named_list <- function(x, what) {
  if (!is.list(x)) {
    return(sprintf("@%s must be a list", what))
  }
  if (length(x) > 0L) {
    nms <- names(x)
    if (is.null(nms) || any(!nzchar(nms))) {
      return(sprintf("@%s must be a named list", what))
    }
  }
  NULL
}

#' @rdname data-model
#' @export
Element <- S7::new_class(
  "Element",
  properties = list(
    type = S7::class_character,
    props = S7::class_list,
    children = S7::class_list
  ),
  constructor = function(type, props = list(), children = list()) {
    S7::new_object(
      S7::S7_object(),
      type = type,
      props = props,
      children = children
    )
  },
  validator = function(self) {
    msg <- .check_type(self@type)
    if (!is.null(msg)) {
      return(msg)
    }
    msg <- .check_named_list(self@props, "props")
    if (!is.null(msg)) {
      return(msg)
    }
    ok <- vapply(
      self@children,
      function(c) is.character(c) && length(c) == 1L && !is.na(c) && nzchar(c),
      logical(1)
    )
    if (length(ok) && !all(ok)) {
      return("@children must be a list of length-1 character element keys")
    }
    NULL
  }
)

#' @rdname data-model
#' @export
Spec <- S7::new_class(
  "Spec",
  properties = list(
    root = S7::class_character,
    elements = S7::class_list
  ),
  constructor = function(root, elements) {
    S7::new_object(S7::S7_object(), root = root, elements = elements)
  },
  validator = function(self) {
    if (
      !is.character(self@root) || length(self@root) != 1L || !nzchar(self@root)
    ) {
      return("@root must be a single non-empty string")
    }
    if (!(self@root %in% names(self@elements))) {
      return(sprintf(
        "@root '%s' not found in elements keys: %s",
        self@root,
        paste(names(self@elements), collapse = ", ")
      ))
    }
    ok <- vapply(
      self@elements,
      function(e) S7::S7_inherits(e, Element),
      logical(1)
    )
    if (length(ok) && !all(ok)) {
      return("@elements must be a named list of Element objects")
    }
    NULL
  }
)

#' @rdname data-model
#' @export
Node <- S7::new_class(
  "Node",
  properties = list(
    type = S7::class_character,
    props = S7::class_list,
    children = S7::class_list
  ),
  validator = function(self) {
    msg <- .check_type(self@type)
    if (!is.null(msg)) {
      return(msg)
    }
    msg <- .check_named_list(self@props, "props")
    if (!is.null(msg)) {
      return(msg)
    }
    ok <- vapply(
      self@children,
      function(c) S7::S7_inherits(c, Node),
      logical(1)
    )
    if (length(ok) && !all(ok)) {
      return("@children must be Node objects")
    }
    NULL
  }
)

#' @rdname data-model
#' @export
element <- function(type, props = list(), children = list()) {
  Element(type = type, props = props, children = children)
}

#' @rdname data-model
#' @export
spec <- function(root, elements) {
  Spec(root = root, elements = elements)
}

#' @rdname data-model
#' @export
node <- function(type, ..., props = list()) {
  children <- list(...)
  bad <- which(
    !vapply(children, function(c) S7::S7_inherits(c, Node), logical(1))
  )
  if (length(bad)) {
    cli::cli_abort(c(
      "`node()` children must be {.cls Node} objects.",
      "x" = "Children at position{?s} {bad} {?is/are} not a Node.",
      "i" = "Pass text via {.arg props} (e.g. props = list(text = \"Hello\")); the registered React component renders it."
    ))
  }
  Node(type = type, props = props, children = children)
}
