# R Wire-Format Rework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the R `shinyreact` package's data model + serializer to emit the #119 nested discriminated-union wire tree (`react`/`tag`/`text`/`html`), walking R htmltools content like Python's `serialize_ui()`, including static mounts and dependency harvesting; remove the obsolete flat-map model (S7 `Spec`/`Element`/`Node`, `to_spec()`, `.wire_json()`).

**Architecture:** A plain S3-classed `node()` (`class = "shinyreact_node"`) plus an internal `as_wire()` S3 generic that walks nodes, htmltools tags/taglists/HTML, strings, numbers, and dependencies into the wire tree. `render_reactive()` walks via `serialize_ui()` and warns on harvested deps; `as.tags.shinyreact_node()` emits a static `.shinyreact-static` mount. Scalars are `jsonlite::unbox()`-wrapped so Shiny's serializer emits JSON scalars. No `Spec`/`Element`/`to_spec`; S7 dropped.

**Tech Stack:** R, htmltools, jsonlite, cli, shiny, testthat (3e), roxygen2, air. Spec: `docs/superpowers/specs/2026-05-29-r-wire-format-rework-design.md`. Python reference: `pkg-py/src/shinyreact/_spec.py` (`_walk`, `serialize_ui`, `Node`), `_reactive_output.py`.

**Verified environment facts (R 4.5.2, htmltools 0.5.9, jsonlite 2.0.0):**
- `as.tags.list` and `as.tags.character` exist → a plain list/character IS as.tags-able, so `.should_walk` must use the precise three-class check, NOT "as.tags succeeds."
- `HTML("x")` has class `c("html","character")` → `is.character()` is `TRUE` for it (bare top-level HTML passes through as raw data, matching Python's `str`-subclass behavior; HTML as a *child* becomes an `html` node via the walker).
- `class(tagList(...))` is `c("shiny.tag.list","list")` → defining only `as_wire.list` covers both bare lists and taglists (UseMethod walks the class vector).
- `class(42)` is `"numeric"`, `class(42L)` is `"integer"`, `class(TRUE)` is `"logical"` → need methods for each.
- `jsonlite::toJSON(structure(list(), names=character()))` → `{}`; `jsonlite::toJSON(list())` → `[]`.
- `jsonlite::unbox()` scalars survive `toJSON(..., auto_unbox = FALSE)` as JSON scalars.

**Refinement vs spec:** the design spec's `.should_walk` mentioned "objects with an as.tags() method are walkable." That is replaced by the precise three-class rule above (Task 7 updates the spec note). This matches Python's actual `_should_walk` behavior.

---

## File Structure

**New:**
- `pkg-r/R/node.R` — `node()` constructor (S3 `shinyreact_node`) + `as.tags.shinyreact_node()` (static mount)
- `pkg-r/R/wire.R` — `as_wire()` S3 generic + methods; `translate_attrs()`; `.wire_props()`; `.walk_all()`; `serialize_ui()`; dep accumulator
- `pkg-r/tests/testthat/test-wire.R`, `test-node.R`, `test-static-mount.R`

**Modified:**
- `pkg-r/R/render.R` — rewrite `.render_transform()` + add `.should_walk()`
- `pkg-r/tests/testthat/test-render.R` — rewrite
- `pkg-r/DESCRIPTION` — remove `S7` from Imports
- `pkg-r/R/shinyreact-package.R` — remove `@import S7`
- `pkg-py/tests/test_wire_fixtures.py` — rewrite to new API
- `pkg-py/tests/fixtures/wire_format/*.json` — replace with new tree fixtures
- `pkg-r/tests/testthat/fixtures/wire_format/*.json` — replace (copies)
- `pkg-r/tests/testthat/test-parity.R` — rewrite
- `docs/features.md`, `docs/todos.md`, `docs/superpowers/specs/2026-05-29-r-wire-format-rework-design.md`, `docs/superpowers/specs/2026-05-26-r-package-design.md`
- `examples/app-r/*`, `examples/ui-tsx-r/*` — re-verify (likely no source change)

**Deleted:**
- `pkg-r/R/spec.R`, `pkg-r/R/to_spec.R`
- `pkg-r/tests/testthat/test-spec.R`, `test-to-spec.R`, `test-wire-json.R`

---

## Conventions

- Single test file: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/<file>")'`
- Full R suite: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_dir("tests/testthat")'`
- Document after roxygen change: `cd pkg-r && Rscript -e 'devtools::document()'`
- Format: `air format pkg-r/` (or `air format <paths>`).
- Commit: do NOT sign — `git -c commit.gpgsign=false commit -m "..."`. Branch `schloerke/r-package-issue`.
- Python: `uv run pytest ...` from repo root.

---

## Task 1: Walker core (`wire.R`) for htmltools content

Build the `as_wire()` walker + helpers for everything EXCEPT `shinyreact_node` (which doesn't exist until Task 2). The old flat-map model stays intact and loadable; this is a standalone new file.

**Files:**
- Create: `pkg-r/R/wire.R`
- Create: `pkg-r/tests/testthat/test-wire.R`

- [ ] **Step 1: Write `pkg-r/tests/testthat/test-wire.R`**

```r
# Parse a single-node walker result to JSON-structure for assertions.
wire1 <- function(x) {
  parts <- serialize_ui(x)
  jsonlite::fromJSON(
    jsonlite::toJSON(parts$payload, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
}

test_that("a plain string becomes a text node", {
  expect_identical(wire1("hello"), list(type = "text", value = "hello"))
})

test_that("a number becomes a stringified text node", {
  expect_identical(wire1(42L), list(type = "text", value = "42"))
  expect_identical(wire1(3.5), list(type = "text", value = "3.5"))
})

test_that("HTML() becomes an html node", {
  expect_identical(
    wire1(htmltools::HTML("<b>x</b>")),
    list(type = "html", html = "<b>x</b>")
  )
})

test_that("a shiny.tag becomes a tag node with translated attrs", {
  out <- wire1(htmltools::tags$span("hi", class = "x", `for` = "y"))
  expect_identical(out$type, "tag")
  expect_identical(out$name, "span")
  expect_identical(out$props$className, "x")
  expect_identical(out$props$htmlFor, "y")
  expect_identical(out$children, list(list(type = "text", value = "hi")))
})

test_that("a tagList of siblings yields an array payload", {
  parts <- serialize_ui(htmltools::tagList(
    htmltools::tags$div("a"),
    htmltools::tags$div("b")
  ))
  parsed <- jsonlite::fromJSON(
    jsonlite::toJSON(parts$payload, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
  expect_length(parsed, 2)
  expect_identical(parsed[[1]]$name, "div")
})

test_that("html dependencies are harvested, not emitted as nodes", {
  dep <- htmltools::htmlDependency("d", "1.0.0", src = c(href = "x"))
  parts <- serialize_ui(htmltools::tagList(htmltools::tags$div("a"), dep))
  expect_length(parts$deps, 1)
  expect_identical(parts$deps[[1]]$name, "d")
  # The dep is not in the payload; only the div remains (single node).
  expect_identical(parts$payload$name, jsonlite::unbox("div"))
})

test_that("NULL and empty content yield an empty payload", {
  expect_identical(serialize_ui(NULL)$payload, list())
  expect_identical(serialize_ui(htmltools::tagList())$payload, list())
})

test_that("empty tag props serialize as an object, children as an array", {
  parts <- serialize_ui(htmltools::tags$hr())
  txt <- jsonlite::toJSON(parts$payload, auto_unbox = FALSE)
  expect_match(txt, '"props":\\{\\}')
  expect_match(txt, '"children":\\[\\]')
})

test_that("an unknown object falls back to as.tags", {
  # A function with an as.tags method: use a shiny.tag.function-like via a
  # simple Tagifiable — htmltools::tagList wraps; here use a bare tag created
  # through as.tags on a character (as.tags.character -> text). Confirms the
  # default path delegates rather than erroring on a known-convertible value.
  # (Plain character is handled directly; this asserts default delegation by
  # constructing an object whose only path is as.tags.)
  obj <- structure(list(), class = "nomethod_xyz")
  expect_error(serialize_ui(obj))  # as.tags.default errors on unconvertible
})
```

- [ ] **Step 2: Run to verify FAIL** (`serialize_ui` not found).

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-wire.R")'`
Expected: FAIL — could not find function "serialize_ui".

- [ ] **Step 3: Write `pkg-r/R/wire.R`**

```r
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
    list(type = jsonlite::unbox("text"), value = jsonlite::unbox(as.character(v)))
  })
}

#' Walk a UI value into wire nodes (internal)
#'
#' S3 generic returning a list of zero-or-more wire nodes. `deps` is a mutable
#' accumulator from [.new_dep_acc()].
#' @keywords internal
as_wire <- function(x, deps) UseMethod("as_wire")

#' @keywords internal
as_wire.shiny.tag <- function(x, deps) {
  list(list(
    type = jsonlite::unbox("tag"),
    name = jsonlite::unbox(x$name),
    props = .tag_props(x),
    children = .walk_all(x$children, deps)
  ))
}

#' @keywords internal
as_wire.list <- function(x, deps) .walk_all(x, deps)

#' @keywords internal
as_wire.html <- function(x, deps) {
  list(list(type = jsonlite::unbox("html"), html = jsonlite::unbox(as.character(x))))
}

#' @keywords internal
as_wire.character <- function(x, deps) .text_nodes(x)

#' @keywords internal
as_wire.numeric <- function(x, deps) .text_nodes(x)

#' @keywords internal
as_wire.integer <- function(x, deps) .text_nodes(x)

#' @keywords internal
as_wire.logical <- function(x, deps) .text_nodes(x)

#' @keywords internal
as_wire.html_dependency <- function(x, deps) {
  deps$deps <- c(deps$deps, list(x))
  list()
}

#' @keywords internal
`as_wire.NULL` <- function(x, deps) list()

#' @keywords internal
as_wire.default <- function(x, deps) {
  # Unknown object: delegate to htmltools::as.tags (errors clearly if there is
  # no method). Mirrors Python's tagify() fallback.
  as_wire(htmltools::as.tags(x), deps)
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
```

- [ ] **Step 4: Run tests to verify PASS**

Run: `cd pkg-r && Rscript -e 'devtools::document(); devtools::load_all("."); testthat::test_file("tests/testthat/test-wire.R")'`
Expected: PASS. If `as_wire.NULL` registration via backtick name doesn't dispatch, confirm with a `serialize_ui(NULL)` check; the backtick form is the standard way to define an S3 method for the `NULL` class.

- [ ] **Step 5: Confirm the old suite still passes (model untouched)**

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_dir("tests/testthat")'`
Expected: PASS (old spec/to_spec tests still green; new wire tests green).

- [ ] **Step 6: Commit**

```bash
air format pkg-r/
cd pkg-r && Rscript -e 'devtools::document()' && cd ..
git add pkg-r/R/wire.R pkg-r/tests/testthat/test-wire.R pkg-r/NAMESPACE pkg-r/man
git -c commit.gpgsign=false commit -m "feat(r): as_wire() walker for htmltools content (#91)"
```

---

## Task 2: Swap the model — new `node()`, rewire `render_reactive`, delete flat-map

This is the atomic swap: the old `node()`/`Spec`/`Element`/`to_spec` and the new `node()` cannot coexist (name clash; `render.R` depends on `to_spec`). Replace in one task so the package stays loadable at the commit.

**Files:**
- Create: `pkg-r/R/node.R`
- Modify: `pkg-r/R/wire.R` (add `as_wire.shinyreact_node`)
- Modify: `pkg-r/R/render.R`
- Modify: `pkg-r/R/shinyreact-package.R` (drop `@import S7`)
- Modify: `pkg-r/DESCRIPTION` (drop `S7`)
- Delete: `pkg-r/R/spec.R`, `pkg-r/R/to_spec.R`
- Delete: `pkg-r/tests/testthat/test-spec.R`, `test-to-spec.R`, `test-wire-json.R`
- Create: `pkg-r/tests/testthat/test-node.R`
- Rewrite: `pkg-r/tests/testthat/test-render.R`

- [ ] **Step 1: Delete the obsolete files**

```bash
cd /Users/barret/conductor/workspaces/shinyreact.nosync/trenton
git rm pkg-r/R/spec.R pkg-r/R/to_spec.R \
       pkg-r/tests/testthat/test-spec.R \
       pkg-r/tests/testthat/test-to-spec.R \
       pkg-r/tests/testthat/test-wire-json.R
```

Note: `.wire_json` (defined in the old `to_spec.R`) is removed. `bookmark.R` used it — Step 6 re-checks bookmark. The bookmark restore payload will use `jsonlite::toJSON(values, auto_unbox = TRUE)` directly (see Step 5).

- [ ] **Step 2: Write `pkg-r/tests/testthat/test-node.R`**

```r
test_that("node() builds an S3 shinyreact_node", {
  n <- node("Card", props = list(title = "Hi"))
  expect_s3_class(n, "shinyreact_node")
  expect_identical(n$type, "Card")
  expect_identical(n$props, list(title = "Hi"))
  expect_identical(n$children, list())
})

test_that("node() collects mixed children via ...", {
  n <- node("Card", node("Divider"), htmltools::tags$span("x"), "text", 42)
  expect_length(n$children, 4)
  expect_s3_class(n$children[[1]], "shinyreact_node")
  expect_s3_class(n$children[[2]], "shiny.tag")
  expect_identical(n$children[[3]], "text")
})

test_that("node() rejects an empty or non-scalar type", {
  expect_error(node(""), "non-empty")
  expect_error(node(c("a", "b")), "single")
})

test_that("node() rejects unnamed props", {
  expect_error(node("X", props = list(1, 2)), "named")
})

test_that("a node walks to a react wire node", {
  parts <- serialize_ui(node("Card", props = list(title = "Hi"), node("Divider")))
  p <- jsonlite::fromJSON(
    jsonlite::toJSON(parts$payload, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
  expect_identical(p$type, "react")
  expect_identical(p$name, "Card")
  expect_identical(p$props$title, "Hi")
  expect_identical(p$children[[1]]$type, "react")
  expect_identical(p$children[[1]]$name, "Divider")
})
```

- [ ] **Step 3: Write `pkg-r/R/node.R`** (constructor only; `as.tags` method comes in Task 3)

```r
#' Create a React component node
#'
#' A `node()` names a registered React component and its props/children.
#' Children may mix other `node()`s, htmltools tags (`tags$div(...)`),
#' `htmltools::HTML()`, strings, and numbers; serialization walks them into the
#' JSON wire tree. Mirrors Python `shinyreact.Node`.
#'
#' @param type Registered component name (single non-empty string).
#' @param ... Children: `node()`s, htmltools tags, `HTML()`, strings, numbers.
#' @param props Named list of props (or empty).
#' @return An object of class `shinyreact_node`.
#' @export
node <- function(type, ..., props = list()) {
  if (!is.character(type) || length(type) != 1L) {
    cli::cli_abort("{.arg type} must be a single string.")
  }
  if (!nzchar(type)) {
    cli::cli_abort("{.arg type} must be a non-empty string.")
  }
  if (length(props) > 0L) {
    nms <- names(props)
    if (is.null(nms) || any(!nzchar(nms))) {
      cli::cli_abort("{.arg props} must be a named list.")
    }
  }
  structure(
    list(type = type, props = props, children = list(...)),
    class = "shinyreact_node"
  )
}
```

- [ ] **Step 4: Add the node method to `pkg-r/R/wire.R`** (append)

```r
#' @keywords internal
as_wire.shinyreact_node <- function(x, deps) {
  list(list(
    type = jsonlite::unbox("react"),
    name = jsonlite::unbox(x$type),
    props = .wire_props(x$props),
    children = .walk_all(x$children, deps)
  ))
}
```

- [ ] **Step 5: Rewrite `pkg-r/R/render.R`**

```r
# Walk only for node/tag/taglist. Bare character (incl. HTML(), which is a
# character subclass) and plain lists/numbers pass through as raw data for
# useShinyOutputValue — matching Python's _should_walk (HTML subclasses str).
.should_walk <- function(value) {
  if (is.character(value)) {
    return(FALSE)
  }
  inherits(value, c("shinyreact_node", "shiny.tag", "shiny.tag.list"))
}

# Value-transform shared by render_reactive() and its tests.
.render_transform <- function(value) {
  if (is.null(value)) {
    return(NULL)
  }
  if (.should_walk(value)) {
    parts <- serialize_ui(value)
    if (length(parts$deps) > 0L) {
      nms <- paste(
        vapply(parts$deps, function(d) d$name, character(1)),
        collapse = ", "
      )
      cli::cli_warn(c(
        "shinyreact output returned content carrying HTMLDependency objects ({nms}) that cannot be injected after the page has rendered.",
        "i" = "Declare them up-front via {.code ui_output(..., extra_deps = list(...))} or at the page level."
      ))
    }
    return(parts$payload)
  }
  value
}

#' Render a React component tree (or raw data) to a shinyreact output
#'
#' Server-side counterpart to `useShinyOutputValue()`. Assign to `output[[id]]`
#' where the UI has a matching [ui_output()]. Accepts a [node()] tree (which may
#' interleave htmltools tags, `HTML()`, and strings) or any JSON-serializable
#' value (passed through unchanged).
#'
#' @param expr An expression returning a `node()` tree / htmltools content, or a
#'   JSON-serializable value.
#' @param env The environment in which to evaluate `expr`.
#' @param quoted Is `expr` already quoted?
#' @return A Shiny render function.
#' @export
render_reactive <- function(expr, env = parent.frame(), quoted = FALSE) {
  func <- shiny::installExprFunction(
    expr, "func",
    eval.env = env, quoted = quoted, label = "render_reactive"
  )
  shiny::createRenderFunction(
    func,
    function(value, session, name, ...) .render_transform(value),
    ui_output
  )
}
```

- [ ] **Step 6: Update `bookmark.R` to not depend on `.wire_json`**

Open `pkg-r/R/bookmark.R`. Find where it called `.wire_json(values)` (Layer 1 of the restore payload) and replace with a direct `jsonlite::toJSON(values, auto_unbox = TRUE)`:

```r
  # Layer 1: JSON of the values; neutralize </ so it can't close <script>.
  json_payload <- gsub(
    "</", "<\\/",
    as.character(jsonlite::toJSON(values, auto_unbox = TRUE)),
    fixed = TRUE
  )
```

(Everything else in `bookmark.R` stays. The known `auto_unbox` shape caveat is already tracked in `docs/todos.md`.)

- [ ] **Step 7: Drop S7 from package metadata**

Edit `pkg-r/DESCRIPTION`: remove the `S7,` line from `Imports:`.
Edit `pkg-r/R/shinyreact-package.R`: remove the `#' @import S7` line (leave the `"_PACKAGE"` block and the usethis namespace markers).

- [ ] **Step 8: Rewrite `pkg-r/tests/testthat/test-render.R`**

```r
test_that(".render_transform walks a node to a react wire tree", {
  val <- shinyreact:::.render_transform(node("Card", props = list(title = "Hi")))
  p <- jsonlite::fromJSON(
    jsonlite::toJSON(val, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
  expect_identical(p$type, "react")
  expect_identical(p$name, "Card")
  expect_identical(p$props$title, "Hi")
})

test_that(".render_transform walks a bare htmltools tag", {
  val <- shinyreact:::.render_transform(htmltools::tags$div("hi"))
  p <- jsonlite::fromJSON(
    jsonlite::toJSON(val, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
  expect_identical(p$type, "tag")
  expect_identical(p$name, "div")
})

test_that(".render_transform passes a raw list through unchanged", {
  expect_identical(
    shinyreact:::.render_transform(list(key = "value", count = 42L)),
    list(key = "value", count = 42L)
  )
})

test_that(".render_transform passes a bare string through unchanged", {
  expect_identical(shinyreact:::.render_transform("raw json string"), "raw json string")
})

test_that(".render_transform returns NULL for NULL", {
  expect_null(shinyreact:::.render_transform(NULL))
})

test_that(".render_transform warns when a walked tree carries dependencies", {
  dep <- htmltools::htmlDependency("d", "1.0.0", src = c(href = "x"))
  expect_warning(
    shinyreact:::.render_transform(node("Card", htmltools::tags$div("a"), dep)),
    "HTMLDependency"
  )
})

test_that("render_reactive returns a shiny render function", {
  r <- render_reactive(node("Card"))
  expect_s3_class(r, "shiny.render.function")
})

test_that("render_reactive produces unboxed scalars over a live session", {
  shiny::testServer(
    app = shiny::shinyApp(
      ui = ui_output("out"),
      server = function(input, output, session) {
        output$out <- render_reactive(node("Card", props = list(title = "Hi")))
      }
    ),
    expr = {
      val <- output$out
      txt <- jsonlite::toJSON(val, auto_unbox = FALSE)
      # Scalars must be JSON scalars, not 1-arrays.
      expect_match(txt, '"name":"Card"')
      expect_match(txt, '"type":"react"')
    }
  )
})
```

Note on the `testServer` block: `output$out` inside `testServer` yields the transformed value (the wire list). If `output$out` returns the value in a form that needs `session$getOutput("out")` instead, adjust to the working accessor for shiny 1.13.0; the assertion is that the serialized output has scalar `name`/`type`. If `testServer` cannot expose the raw value pre-serialization, assert on `shinyreact:::.render_transform(node("Card", props=list(title="Hi")))` serialized instead, and keep the `shiny.render.function` class test for the wiring. The goal: confirm scalars are unboxed in the emitted JSON.

- [ ] **Step 9: Document, run, verify**

Run: `cd pkg-r && Rscript -e 'devtools::document(); devtools::load_all("."); testthat::test_dir("tests/testthat")'`
Expected: PASS — `test-node.R`, `test-wire.R`, `test-render.R` green; no references to removed `Spec`/`Element`/`to_spec`/`.wire_json`. The package loads with no S7.

If load fails because some file still references `to_spec`/`Spec`/`Element`/`.wire_json`, grep and fix:
`grep -rn "to_spec\|\.wire_json\|S7::\|Spec\|Element" pkg-r/R` — only legitimate hits (e.g. none) should remain.

- [ ] **Step 10: Commit**

```bash
air format pkg-r/
cd pkg-r && Rscript -e 'devtools::document()' && cd ..
git add -A pkg-r
git -c commit.gpgsign=false commit -m "refactor(r)!: node() S3 + walker render; drop flat-map Spec/Element/to_spec (#91)"
```

---

## Task 3: Static mounts — `as.tags.shinyreact_node()`

**Files:**
- Modify: `pkg-r/R/node.R` (add the method)
- Create: `pkg-r/tests/testthat/test-static-mount.R`

- [ ] **Step 1: Write `pkg-r/tests/testthat/test-static-mount.R`**

```r
test_that("as.tags.shinyreact_node emits a static mount with inline JSON", {
  tagobj <- htmltools::as.tags(node("Card", props = list(title = "Hi")))
  html <- as.character(tagobj)
  expect_match(html, 'class="shinyreact-static"')
  expect_match(html, 'type="application/json"')
  # The component name appears in the inline spec.
  expect_match(html, "Card")
  # The shinyreact dependency rides along.
  deps <- htmltools::findDependencies(tagobj)
  expect_true(any(vapply(deps, function(d) d$name == "shinyreact", logical(1))))
})

test_that("static mount escapes < to prevent </script> breakout", {
  tagobj <- htmltools::as.tags(node("Card", htmltools::HTML("</script><b>x</b>")))
  html <- as.character(tagobj)
  # No literal </script> inside the inline JSON payload.
  # The inline JSON encodes < as \\u003c.
  expect_match(html, "u003c", fixed = TRUE)
})

test_that("static mount surfaces harvested dependencies", {
  dep <- htmltools::htmlDependency("extra", "1.0.0", src = c(href = "x"))
  tagobj <- htmltools::as.tags(node("Card", htmltools::tags$div("a"), dep))
  deps <- htmltools::findDependencies(tagobj)
  names <- vapply(deps, function(d) d$name, character(1))
  expect_true(all(c("shinyreact", "extra") %in% names))
})
```

- [ ] **Step 2: Run to verify FAIL** (no `as.tags` method → it'd hit `as.tags.default` and error or mis-handle).

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-static-mount.R")'`
Expected: FAIL.

- [ ] **Step 3: Append `as.tags.shinyreact_node` to `pkg-r/R/node.R`**

```r
#' @rdname node
#' @param x A `shinyreact_node`.
#' @exportS3Method htmltools::as.tags
as.tags.shinyreact_node <- function(x, ...) {
  parts <- serialize_ui(x)
  # Escape "<" as < (valid JSON, parses back to "<") so a payload with
  # "</script>" can't break out of the inline <script>. Mirrors Python's
  # Node.tagify().
  spec_json <- gsub(
    "<", "\\u003c",
    as.character(jsonlite::toJSON(parts$payload, auto_unbox = FALSE)),
    fixed = TRUE
  )
  htmltools::tagList(
    shinyreact_dep(),
    parts$deps,
    htmltools::div(
      class = "shinyreact-static",
      htmltools::tags$script(htmltools::HTML(spec_json), type = "application/json")
    )
  )
}
```

Note: `@exportS3Method htmltools::as.tags` registers the S3 method in NAMESPACE so htmltools' `as.tags` generic dispatches to it. If `parts$deps` (a list of dependency objects) is not flattened by `tagList`, splice it: replace `parts$deps,` with `!!!parts$deps` is not available without rlang — instead use `do.call(htmltools::tagList, c(list(shinyreact_dep()), parts$deps, list(htmltools::div(...))))`. Verify which form makes `findDependencies` surface both deps; the test is the source of truth.

- [ ] **Step 4: Run tests to verify PASS**

Run: `cd pkg-r && Rscript -e 'devtools::document(); devtools::load_all("."); testthat::test_file("tests/testthat/test-static-mount.R")'`
Expected: PASS. Confirm NAMESPACE gained `S3method(as.tags,shinyreact_node)` (or the registered export).

- [ ] **Step 5: Full suite + commit**

```bash
cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_dir("tests/testthat")'
air format pkg-r/
cd pkg-r && Rscript -e 'devtools::document()' && cd ..
git add pkg-r/R/node.R pkg-r/tests/testthat/test-static-mount.R pkg-r/NAMESPACE pkg-r/man
git -c commit.gpgsign=false commit -m "feat(r): as.tags.shinyreact_node() static mount (#91)"
```

---

## Task 4: Regenerate Python wire fixtures + fix the broken test

**Files:**
- Rewrite: `pkg-py/tests/test_wire_fixtures.py`
- Replace: `pkg-py/tests/fixtures/wire_format/*.json` (delete old 5, write new 6)

- [ ] **Step 1: Remove the old fixtures**

```bash
cd /Users/barret/conductor/workspaces/shinyreact.nosync/trenton
git rm pkg-py/tests/fixtures/wire_format/single_element.json \
       pkg-py/tests/fixtures/wire_format/nested_tree.json \
       pkg-py/tests/fixtures/wire_format/empty_children.json \
       pkg-py/tests/fixtures/wire_format/multi_props.json \
       pkg-py/tests/fixtures/wire_format/raw_value.json
```

- [ ] **Step 2: Write `pkg-py/tests/test_wire_fixtures.py`** (new API, generates + asserts)

```python
import json
from pathlib import Path

from htmltools import HTML, TagList, tags

import shinyreact

FIXTURES = Path(__file__).parent / "fixtures" / "wire_format"


def _wire(value: object) -> object:
    if isinstance(value, shinyreact.Node):
        return value.to_dict()
    from shinyreact._spec import serialize_ui

    payload, _deps = serialize_ui(value)
    return payload


# name -> (value producing the wire payload)
def _cases() -> dict[str, object]:
    return {
        "react_node": shinyreact.Node(type="Card", props={"title": "Hi"}),
        "tag_child": shinyreact.Node(
            type="Card", children=[tags.span("hi", class_="x")]
        ),
        "text_child": shinyreact.Node(type="Card", children=["plain text", 42]),
        "html_child": shinyreact.Node(type="Card", children=[HTML("<b>x</b>")]),
        "mixed_tree": shinyreact.Node(
            type="Card",
            props={"title": "Hi"},
            children=[
                shinyreact.Node(type="Divider"),
                tags.span("hi", class_="x"),
                "text",
            ],
        ),
        "taglist_root": TagList(
            shinyreact.Node(type="Card"), tags.div("d", id="root2")
        ),
    }


def test_fixtures_match_committed() -> None:
    for name, value in _cases().items():
        expected = json.loads((FIXTURES / f"{name}.json").read_text())
        assert _wire(value) == expected, name
```

- [ ] **Step 3: Generate the fixture files** from the same cases

```bash
cd /Users/barret/conductor/workspaces/shinyreact.nosync/trenton
uv run python -c '
import json
from pathlib import Path
from htmltools import HTML, TagList, tags
import shinyreact
from shinyreact._spec import serialize_ui

def wire(value):
    if isinstance(value, shinyreact.Node):
        return value.to_dict()
    payload, _ = serialize_ui(value)
    return payload

cases = {
    "react_node": shinyreact.Node(type="Card", props={"title":"Hi"}),
    "tag_child": shinyreact.Node(type="Card", children=[tags.span("hi", class_="x")]),
    "text_child": shinyreact.Node(type="Card", children=["plain text", 42]),
    "html_child": shinyreact.Node(type="Card", children=[HTML("<b>x</b>")]),
    "mixed_tree": shinyreact.Node(type="Card", props={"title":"Hi"}, children=[
        shinyreact.Node(type="Divider"), tags.span("hi", class_="x"), "text"]),
    "taglist_root": TagList(shinyreact.Node(type="Card"), tags.div("d", id="root2")),
}
out = Path("pkg-py/tests/fixtures/wire_format")
for name, value in cases.items():
    (out / f"{name}.json").write_text(json.dumps(wire(value), indent=2) + "\n")
print("wrote", len(cases))
'
```

- [ ] **Step 4: Run the Python test + suite**

Run: `uv run pytest pkg-py/tests/test_wire_fixtures.py -v`
Expected: PASS. Then `uv run pytest pkg-py/tests -q` — expected PASS (this clears the merge-introduced failure). Inspect `cat pkg-py/tests/fixtures/wire_format/mixed_tree.json` to record the canonical shape.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/tests/fixtures/wire_format pkg-py/tests/test_wire_fixtures.py
git -c commit.gpgsign=false commit -m "test(py): regenerate wire fixtures for discriminated-union tree (#91)"
```

---

## Task 5: Rewrite the R parity test

**Files:**
- Replace: `pkg-r/tests/testthat/fixtures/wire_format/*.json` (copy from pkg-py)
- Rewrite: `pkg-r/tests/testthat/test-parity.R`

- [ ] **Step 1: Refresh the R fixture copies**

```bash
cd /Users/barret/conductor/workspaces/shinyreact.nosync/trenton
rm -f pkg-r/tests/testthat/fixtures/wire_format/*.json
cp pkg-py/tests/fixtures/wire_format/*.json pkg-r/tests/testthat/fixtures/wire_format/
```

- [ ] **Step 2: Rewrite `pkg-r/tests/testthat/test-parity.R`**

```r
# Fixtures are copies of pkg-py/tests/fixtures/wire_format/ — kept in sync by
# `make r-check-fixtures`. Python is the source of truth; R must reproduce the
# same wire tree (compared semantically; whitespace/format-insignificant).

fixture <- function(name) {
  jsonlite::fromJSON(
    testthat::test_path("fixtures", "wire_format", paste0(name, ".json")),
    simplifyVector = FALSE
  )
}

r_wire <- function(value) {
  parts <- serialize_ui(value)
  jsonlite::fromJSON(
    jsonlite::toJSON(parts$payload, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
}

test_that("react_node matches Python", {
  expect_equal(r_wire(node("Card", props = list(title = "Hi"))), fixture("react_node"))
})

test_that("tag_child matches Python (attr translation)", {
  expect_equal(
    r_wire(node("Card", htmltools::tags$span("hi", class = "x"))),
    fixture("tag_child")
  )
})

test_that("text_child matches Python (number coercion)", {
  expect_equal(
    r_wire(node("Card", "plain text", 42L)),
    fixture("text_child")
  )
})

test_that("html_child matches Python", {
  expect_equal(
    r_wire(node("Card", htmltools::HTML("<b>x</b>"))),
    fixture("html_child")
  )
})

test_that("mixed_tree matches Python", {
  expect_equal(
    r_wire(node(
      "Card",
      node("Divider"),
      htmltools::tags$span("hi", class = "x"),
      "text",
      props = list(title = "Hi")
    )),
    fixture("mixed_tree")
  )
})

test_that("taglist_root matches Python (sibling-list payload)", {
  expect_equal(
    r_wire(htmltools::tagList(node("Card"), htmltools::tags$div("d", id = "root2"))),
    fixture("taglist_root")
  )
})
```

- [ ] **Step 3: Run the parity test**

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-parity.R")'`
Expected: PASS. If a case mismatches, it indicates a REAL R↔Python divergence — inspect `str(r_wire(...))` vs `str(fixture(...))`. Common culprits to check before "fixing" the test: attr key translation (`class`→`className`), number→string coercion (`42`→`"42"`), `props` empty `{}` vs `[]`, children array order. Fix the R walker, not the assertion. If `text_child` differs because R `node("Card","plain text",42L)` vs Python `["plain text", 42]` produce different `value` types, confirm both emit `{"type":"text","value":"42"}` (string).

- [ ] **Step 4: Fixture sync + commit**

```bash
cd /Users/barret/conductor/workspaces/shinyreact.nosync/trenton
make r-check-fixtures   # diff -r must be clean
air format pkg-r/
git add pkg-r/tests/testthat/fixtures pkg-r/tests/testthat/test-parity.R
git -c commit.gpgsign=false commit -m "test(r): rewrite wire-format parity for discriminated-union tree (#91)"
```

---

## Task 6: Re-verify examples

The example `app.R` files use `node()` with `type`/`props`/children — the call sites are unchanged; only the serialization underneath changed. Confirm they still build and (optionally) add one htmltools-nesting demo.

**Files:**
- Verify (likely no change): `examples/app-r/01-hello-world/app.R`, `examples/app-r/02-inputs/app.R`, `examples/app-r/04-messages/app.R`, `examples/ui-tsx-r/01-hello/app.R`
- Optional: one example child uses a raw `htmltools::tags$...` inside a `node()`

- [ ] **Step 1: Install the local package**

```bash
cd /Users/barret/conductor/workspaces/shinyreact.nosync/trenton
Rscript -e 'devtools::install("pkg-r", quiet=TRUE, upgrade="never")'
```

- [ ] **Step 2: Build each example app object**

For each of the four example dirs, from that dir:

```bash
Rscript -e 'app <- source("app.R", local=new.env())$value; stopifnot(inherits(app, "shiny.appobj")); cat("APP OK\n")'
```

Expected: "APP OK" for all four. The `node()` helper definitions inside each `app.R` still work (same constructor signature). If any example referenced removed symbols (`spec`/`element`/`to_spec`), update it to `node()`-only — grep each `app.R` for `spec(`/`element(`/`to_spec(` first; the examples only used `node()` helpers, so none expected.

- [ ] **Step 3: (Optional) htmltools-nesting demo**

In `examples/app-r/01-hello-world/app.R`, change one `node()` child to demonstrate raw htmltools nesting — e.g. wrap a label in `htmltools::tags$small(...)` inside a `node("Card", ...)`. Keep it minimal; rebuild and confirm "APP OK". Skip if it complicates the example without clear value.

- [ ] **Step 4: Commit (only if examples changed)**

```bash
cd /Users/barret/conductor/workspaces/shinyreact.nosync/trenton
air format examples/app-r examples/ui-tsx-r
git add examples/app-r examples/ui-tsx-r
git -c commit.gpgsign=false commit -m "docs(r): verify examples under discriminated-union wire format (#91)"
```

If no example source changed, skip the commit and note "examples build unchanged" in the task report.

---

## Task 7: Docs, spec updates, final verification

**Files:**
- Modify: `docs/features.md`
- Modify: `docs/todos.md`
- Modify: `docs/superpowers/specs/2026-05-29-r-wire-format-rework-design.md` (refine `.should_walk` note)
- Modify: `docs/superpowers/specs/2026-05-26-r-package-design.md` (point data-model/wire sections at the rework)

- [ ] **Step 1: Update `docs/features.md` R section**

Read it. Remove any mention of `spec()`/`element()`/`to_spec()` and the flat-map. Describe the new model: `node()` interleaves React components with htmltools tags / `HTML()` / strings; `render_reactive()` walks the tree; static mounts via embedding `node()` in page chrome. Keep the canonical terminology (app.R / ui.tsx patterns). Keep it concise and consistent with the Python table style.

- [ ] **Step 2: Resolve stale todos in `docs/todos.md`**

Read it. Remove the "R package wire format must follow #119" entry (now done) and the "R `to_spec()` on a child-bearing bare `Element`" entry (the flat `Element` model is gone). Keep the "R bookmark restore value shape vs Python (#27)" entry (still valid — bookmark still uses `auto_unbox = TRUE`).

- [ ] **Step 3: Refine the `.should_walk` note in the rework spec**

Edit `docs/superpowers/specs/2026-05-29-r-wire-format-rework-design.md`: in the `render_reactive()` section, replace the "objects that implement an `as.tags()` method (Tagifiable-like)" clause with the precise rule actually implemented: walk only `shinyreact_node`/`shiny.tag`/`shiny.tag.list`; a bare `character` (incl. `HTML()`) and plain lists/numbers pass through as raw data — matching Python's `_should_walk` (where `HTML` subclasses `str`). Note that `as.tags.list`/`as.tags.character` exist, which is why an "as.tags-able" test would wrongly walk raw data.

- [ ] **Step 4: Cross-link the original R spec**

Edit `docs/superpowers/specs/2026-05-26-r-package-design.md`: add a top note that the data-model / wire-format / `to_spec` / `Spec`/`Element` sections are SUPERSEDED by `2026-05-29-r-wire-format-rework-design.md` (the flat-map was replaced by the #119 discriminated-union tree). Don't rewrite the whole file — one clear pointer at the top.

- [ ] **Step 5: Final full verification**

```bash
cd /Users/barret/conductor/workspaces/shinyreact.nosync/trenton
make r-check-fixtures
cd pkg-r && Rscript -e 'devtools::document(); devtools::load_all("."); testthat::test_dir("tests/testthat")' && cd ..
make r-check 2>&1 | tail -25
uv run pytest pkg-py/tests -q 2>&1 | tail -10
```

Expected:
- `make r-check-fixtures`: clean (no diff).
- R suite: all PASS.
- `make r-check`: `0 errors | 0 warnings | 1 note` (the accepted `shiny:::` bookmark note — and NO new note about S7 being an unused Import, since S7 was removed). If a new NOTE appears (e.g. `as_wire`/`serialize_ui` "no visible global" or undocumented), resolve it (add `@keywords internal` + re-document, or `importFrom`).
- Python suite: all PASS.

- [ ] **Step 6: Commit**

```bash
air format pkg-r/
git add docs/features.md docs/todos.md \
        docs/superpowers/specs/2026-05-29-r-wire-format-rework-design.md \
        docs/superpowers/specs/2026-05-26-r-package-design.md
git -c commit.gpgsign=false commit -m "docs(r): update features/todos/specs for wire-format rework (#91)"
```

---

## Self-Review Notes

**Spec coverage:**
- S3 `node()` (no S7) → Task 2; static mount `as.tags` → Task 3
- `as_wire()` walker (node/tag/taglist/html/text/number/dep/null/default→as.tags) + attr translation + scalar unbox + `serialize_ui` → Tasks 1, 2
- `render_reactive()` rewrite + `.should_walk` (precise three-class) + dep warning → Task 2
- Remove `Spec`/`Element`/`to_spec`/`.wire_json` + S7 → Task 2
- Expanded cross-language fixtures + fix broken Python test → Task 4; R parity rewrite → Task 5; `make r-check-fixtures` → Task 5/7
- Examples re-verified → Task 6
- Docs + spec updates + `R CMD check` green → Task 7

**Deviation from spec (documented):** `.should_walk` uses the precise three-class rule, not "as.tags-able objects" (verified: `as.tags.list`/`as.tags.character` exist; the broad rule would walk raw `ui.tsx` data). Task 7 Step 3 updates the spec note. This matches Python's real `_should_walk`.

**Type/name consistency:** `as_wire`, `serialize_ui`, `translate_attrs`, `.wire_props`, `.tag_props`, `.walk_all`, `.text_nodes`, `.new_dep_acc`, `node`, `as.tags.shinyreact_node`, `.should_walk`, `.render_transform`, `render_reactive` used consistently. Class string `"shinyreact_node"` consistent across constructor, walker method, and `as.tags` method. Wire node shapes (`type`/`name`/`props`/`children`, `type`/`value`, `type`/`html`) match the JS `js/src/spec.ts` discriminated union throughout.

**No placeholders:** every code step contains complete R/Python code. The `testServer` accessor (Task 2 Step 8) and the `tagList` dep-splicing (Task 3 Step 3) carry explicit fallbacks tied to the test as source of truth.
