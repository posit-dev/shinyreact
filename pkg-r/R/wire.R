# Walk R UI content into the shinyreact discriminated-union wire tree.
# Mirrors pkg-py/src/shinyreact/_spec.py (_walk / serialize_ui).

# HTML attribute name -> React prop name. Anything not listed (incl. data-*,
# aria-*) passes through verbatim. Mirrors Python's _ATTR_MAP.
.ATTR_MAP <- c(
  "class" = "className",
  "for" = "htmlFor",
  "tabindex" = "tabIndex",
  "colspan" = "colSpan",
  "rowspan" = "rowSpan",
  "maxlength" = "maxLength",
  "readonly" = "readOnly",
  "autofocus" = "autoFocus",
  "contenteditable" = "contentEditable"
)

translate_attrs <- function(attrs) {
  if (length(attrs) == 0L) {
    return(attrs)
  }
  nms <- names(attrs)
  mapped <- ifelse(nms %in% names(.ATTR_MAP), .ATTR_MAP[nms], nms)
  names(attrs) <- mapped
  attrs
}

# Wrap length-1 atomic values in unbox() so they serialize as JSON scalars.
# Empty -> a names()-tagged empty list so it serializes as {} not [].
.wire_props <- function(props) {
  if (length(props) == 0L) {
    return(structure(list(), names = character()))
  }
  lapply(props, function(v) {
    if (is.atomic(v) && length(v) == 1L) jsonlite::unbox(v) else v
  })
}

# Merge a tag's attributes by unique name (htmltools joins duplicates, e.g.
# multiple class= entries), then translate keys.
.tag_props <- function(tag) {
  nms <- unique(names(tag$attribs))
  nms <- nms[!is.na(nms) & nzchar(nms)]
  if (length(nms) == 0L) {
    return(structure(list(), names = character()))
  }
  vals <- lapply(nms, function(n) htmltools::tagGetAttribute(tag, n))
  names(vals) <- nms
  .wire_props(translate_attrs(vals))
}

# Mutable accumulator for harvested HTMLDependency objects.
.new_dep_acc <- function() {
  e <- new.env(parent = emptyenv())
  e$deps <- list()
  e
}

# Walk a list of children into a flat list of zero-or-more wire nodes.
.walk_all <- function(children, deps) {
  out <- list()
  for (ch in children) {
    out <- c(out, as_wire(ch, deps))
  }
  out
}

.text_nodes <- function(x) {
  lapply(x, function(v) {
    list(
      type = jsonlite::unbox("text"),
      value = jsonlite::unbox(as.character(v))
    )
  })
}

#' Walk a UI value into wire nodes (internal)
#'
#' S3 generic returning a list of zero-or-more wire nodes. `deps` is a mutable
#' environment accumulator for harvested `HTMLDependency` objects.
#' @keywords internal
as_wire <- function(x, deps) UseMethod("as_wire")

#' @keywords internal
#' @exportS3Method
as_wire.shiny.tag <- function(x, deps) {
  list(list(
    type = jsonlite::unbox("tag"),
    name = jsonlite::unbox(x$name),
    props = .tag_props(x),
    children = .walk_all(x$children, deps)
  ))
}

#' @keywords internal
#' @exportS3Method
as_wire.list <- function(x, deps) .walk_all(x, deps)

#' @keywords internal
#' @exportS3Method
as_wire.html <- function(x, deps) {
  list(list(
    type = jsonlite::unbox("html"),
    html = jsonlite::unbox(as.character(x))
  ))
}

#' @keywords internal
#' @exportS3Method
as_wire.character <- function(x, deps) .text_nodes(x)

#' @keywords internal
#' @exportS3Method
as_wire.numeric <- function(x, deps) .text_nodes(x)

#' @keywords internal
#' @exportS3Method
as_wire.integer <- function(x, deps) .text_nodes(x)

#' @keywords internal
#' @exportS3Method
as_wire.logical <- function(x, deps) .text_nodes(x)

#' @keywords internal
#' @exportS3Method
as_wire.html_dependency <- function(x, deps) {
  deps$deps <- c(deps$deps, list(x))
  list()
}

#' @keywords internal
#' @exportS3Method
`as_wire.NULL` <- function(x, deps) list()

#' @keywords internal
#' @exportS3Method
as_wire.default <- function(x, deps) {
  # Try htmltools::as.tags first (works for objects with a tagify/as.tags
  # method). If the result is an empty tagList AND the input was not already a
  # tagList-like (length > 0), fall through to a hard error so callers get a
  # clear message instead of silently rendering nothing.
  # Mirrors Python's tagify() fallback, which only succeeds if the object has
  # a tagify() method.
  cl <- class(x)
  # Check for a real as.tags / tagify method on this class (not just .default).
  has_method <- any(
    vapply(
      cl,
      function(c) {
        !is.null(utils::getS3method("as.tags", c, optional = TRUE)) ||
          !is.null(utils::getS3method("tagify", c, optional = TRUE))
      },
      logical(1)
    )
  )
  if (has_method) {
    return(as_wire(htmltools::as.tags(x), deps))
  }
  stop(
    sprintf(
      "Don't know how to walk an object of class %s into wire nodes.",
      paste(cl, collapse = "/")
    ),
    call. = FALSE
  )
}

#' @keywords internal
#' @exportS3Method
as_wire.shinyreact_node <- function(x, deps) {
  list(list(
    type = jsonlite::unbox("react"),
    name = jsonlite::unbox(x$type),
    props = .wire_props(x$props),
    children = .walk_all(x$children, deps)
  ))
}

#' Serialize a UI value to a wire payload + harvested dependencies (internal)
#'
#' @keywords internal
serialize_ui <- function(value) {
  deps <- .new_dep_acc()
  nodes <- as_wire(value, deps)
  payload <- if (length(nodes) == 1L) nodes[[1]] else nodes
  list(payload = payload, deps = deps$deps)
}
