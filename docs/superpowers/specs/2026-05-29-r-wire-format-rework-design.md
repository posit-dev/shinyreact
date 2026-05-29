# R Wire-Format Rework Design — conform to #119 (discriminated-union tree)

**Issue:** [#91](https://github.com/posit-dev/shinyreact/issues/91) (R package), follows [#119](https://github.com/posit-dev/shinyreact/pull/119) / [#88](https://github.com/posit-dev/shinyreact/issues/88) (wire-format redesign)
**Status:** Design — awaiting implementation plan
**Supersedes:** the flat-map portions of `docs/superpowers/specs/2026-05-26-r-package-design.md`

## Background

The initial R package (`pkg-r/`) was built against the **old flat-map wire format**: a `Spec` of `{root, elements: {key: {type, props, children: [keys]}}}` with auto-generated keys, modeled in R as S7 classes `Spec`/`Element`/`Node` plus a `to_spec()` generic that flattened a nested `Node` into that map.

PR #119 ("layer all the way down") replaced that entirely on the Python + JS side:

- **Removed `Spec`/`Element`** from the Python surface — `Node` is the only spec surface.
- **New nested discriminated-union wire tree.** Four node kinds:
  - `{"type":"react","name":<component>,"props":{...},"children":[...]}`
  - `{"type":"tag","name":<dom-tag>,"props":{...},"children":[...]}`
  - `{"type":"text","value":<string>}`
  - `{"type":"html","html":<raw-html-string>}`
  - Root payload is a single node **or** an array of sibling nodes (e.g. a `TagList`).
- **htmltools tags and the React spec nest at arbitrary depth.** A universal walker (`serialize_ui`/`_walk` in `pkg-py/src/shinyreact/_spec.py`) converts a mixed tree (Nodes, htmltools `Tag`/`TagList`/`HTML`, strings, numbers) and **harvests `HTMLDependency`** objects out of it.
- **Static mounts.** `Node.tagify()` emits a `.shinyreact-static` div + inline `<script type="application/json">`, hydrated client-side by `seedInlineSpecs()` (no output binding, no server round-trip).
- The JS bundle (already current in `pkg-r/inst/lib/shiny/`) renders this union and seeds static mounts.

The R package's server-side serialization is now incompatible with the shipped JS bundle. This spec defines the rework to conform.

## Goal

Rework the R package's **data model + serializer** to emit the #119 discriminated-union wire tree, walking R htmltools content the way Python's `serialize_ui()` does, including static mounts and dependency harvesting. Keep the rest of the package (page helpers, `ui_output`, `send_message`, deps, bookmarking) intact.

## Non-goals

- Re-deriving the JS bundle (already current after the `origin/main` merge).
- Changing `ui_output`, `send_message`, `page_*`, deps, or bookmarking behavior.
- CRAN prep, `ImageOutput`/`render.plot`, Playwright e2e (still out of scope per the original R spec).

## Decisions (from brainstorming)

1. **`node()` is a plain S3-classed list** (`class = "shinyreact_node"`), not S7. With `Spec`/`Element` gone and no validators/typed-accessor hierarchy left, S7 buys nothing; an S3-classed list matches how htmltools models tags and lets the walker dispatch uniformly. S7 is dropped from `DESCRIPTION`.
2. **No `to_spec()` / no public serialization generic.** A single internal walker (`as_wire()` S3 generic) handles everything. Downstream extends by building `node("TheirComponent", ...)` or by implementing `as.tags()` for their class (R's idiomatic escape hatch, mirroring Python's `tagify()` fallback).
3. **Static mounts ship in v1** via `as.tags.shinyreact_node()`, so `node()` works in page chrome as well as in `render_reactive`. Matches what #119 shipped.
4. **Scalars are `unbox()`-wrapped** in walker output so both Shiny's output serializer and the static-mount serializer emit JSON scalars, not 1-element arrays (R vector/scalar ambiguity; Python gets this free).
5. **Cross-language parity via expanded shared fixtures.** Python is the source of truth; fixtures cover all four node kinds + attr translation + sibling-list root; both a Python test and an R test reproduce them.

## Architecture

### What changes vs. what stays

**Removed:** S7 classes `Spec`/`Element`/`Node`; `spec()`/`element()`; `to_spec()` generic + flat-map output; `.wire_json()` flat-map handling; `S7` from `DESCRIPTION` Imports and `@import S7`.

**Reworked:** `node()` (S3 `shinyreact_node`); new internal walker `as_wire()`; `render_reactive()` value-transform; new `as.tags.shinyreact_node()`.

**Unchanged:** `ui_output()`, `send_message()`, `page_bare`/`page_react`/`page_react_html`/`page_react_dep`, `dep.R`, `bookmark.R`. Bookmark keeps its own small JSON serializer for the input-value map (decoupled from the removed flat-map). Page helpers must surface dependencies harvested from any embedded static mounts (already handled by htmltools dependency resolution since `as.tags.shinyreact_node` attaches them).

### Module layout (`pkg-r/R/`)

| File | Contents |
|---|---|
| `node.R` | `node()` constructor (S3 `shinyreact_node`); `as.tags.shinyreact_node()` static mount |
| `wire.R` | `as_wire()` S3 generic + methods; `translate_attrs()`; scalar-unbox helper; `serialize_ui()` (→ `list(payload, deps)`) |
| `render.R` | `render_reactive()` + `.render_transform()` + `.should_walk()` (rewritten) |
| `output.R`, `page.R`, `dep.R`, `message.R`, `bookmark.R` | unchanged |
| ~~`spec.R`, `to_spec.R`~~ | deleted |

## The walker (`as_wire()`)

Internal S3 generic. `as_wire(x, deps)` returns a **list of zero-or-more wire nodes** (a list because `tagList`/vectors flatten to several, and `NULL`/dependencies flatten to none). `deps` is an accumulator (an environment holding a growing list) that harvests `html_dependency` objects from anywhere in the tree.

Dispatch (mirrors Python `_walk`):

| R input | Wire output |
|---|---|
| `shinyreact_node` | `list(type="react", name=<type>, props=<props>, children=<walk children>)` |
| `shiny.tag` | `list(type="tag", name=tag$name, props=translate_attrs(tag$attribs), children=<walk tag$children>)` |
| `shiny.tag.list` / bare `list` | flatten — `as_wire()` each element, concatenate |
| `html` (from `HTML()`) | `list(type="html", html=as.character(x))` |
| `character` length 1 | `list(type="text", value=x)` |
| `character` length >1 / `numeric` / `logical` | one `text` node per element, coerced to string (matches Python per-child) |
| `html_dependency` | append to `deps`, return `list()` |
| `NULL` | `list()` |
| anything else | `as_wire(htmltools::as.tags(x), deps)` — escape hatch |

**`translate_attrs()`** — named map mirroring Python's `_ATTR_MAP`: `class`→`className`, `for`→`htmlFor`, `tabindex`→`tabIndex`, `colspan`→`colSpan`, `rowspan`→`rowSpan`, `maxlength`→`maxLength`, `readonly`→`readOnly`, `autofocus`→`autoFocus`, `contenteditable`→`contentEditable`. Other keys (incl. `data-*`/`aria-*`) pass through. Attrib *values* pass through after key translation; length-1 string values are `unbox()`-wrapped; `NA`/boolean attrs serialize per jsonlite (`true`/`null`).

**Scalar unboxing** — every scalar field emitted (`type`, `name`, `value`, `html`, and each length-1 string/number/bool prop value) is wrapped in `jsonlite::unbox()`.

**`serialize_ui(value)`** (top-level entry, mirrors Python): walk `value`; payload is the single node if the walk yielded one, the list if several (sibling/`TagList` root), or `list()` if none. Returns `list(payload = <payload>, deps = <harvested>)`.

## `node()` + static mounts

```r
node(type, ..., props = list())
# structure(list(type=, props=, children=list(...)), class = "shinyreact_node")
```

Children via `...`, mixing nodes / htmltools tags / `HTML()` / strings / numbers. Light validation: `type` is a single non-empty string; `props` is a named list or empty. Children are not class-validated (the walker accepts htmltools-like content; genuinely unconvertible objects error via the `as.tags` fallback).

**`as.tags.shinyreact_node(x, ...)`** (mirrors Python `Node.tagify()`):

1. `parts <- serialize_ui(x)`.
2. JSON-encode `parts$payload`, escaping `<` as `<` (so a payload containing `</script>` cannot break out of the inline script).
3. Return `tagList(shinyreact_dep(), parts$deps, div(class="shinyreact-static", tags$script(<json>, type="application/json")))`.

The bundle's `seedInlineSpecs()` finds `.shinyreact-static`, parses the adjacent inline JSON, and renders it. This is a distinct path from the walker: inside `render_reactive` a node becomes a `react` wire node over the WebSocket; as UI chrome it becomes a static mount. The walker has an explicit `shinyreact_node` method, so it never recurses through `as.tags` — no loop, no path confusion.

## `render_reactive()`

Keeps its signature and Shiny wiring (`installExprFunction` + `createRenderFunction` + `ui_output` as auto-UI). Rewritten value-transform mirrors Python's `transform` + `_should_walk`:

```r
.should_walk <- function(value) {
  if (is.character(value)) return(FALSE)        # ui.tsx raw JSON string passthrough
  inherits(value, c("shinyreact_node", "shiny.tag", "shiny.tag.list"))
  # plus: objects with an as.tags() method are walkable too — see note below.
}

.render_transform <- function(value) {
  if (is.null(value)) return(NULL)
  if (.should_walk(value)) {
    parts <- serialize_ui(value)
    if (length(parts$deps) > 0) {
      nms <- paste(vapply(parts$deps, function(d) d$name, character(1)), collapse = ", ")
      cli::cli_warn(c(
        "shinyreact output returned content carrying HTMLDependency objects ({nms}) that cannot be injected after the page has rendered.",
        i = "Declare them up-front via {.code ui_output(..., extra_deps = list(...))} or at the page level."
      ))
    }
    return(parts$payload)
  }
  value   # raw JSON passthrough (dict/list/number → useShinyOutputValue)
}
```

`.should_walk` is an internal **S3 generic** with the following dispatch:

- `shinyreact_node` → `TRUE` (walk as a `react` wire node)
- `shiny.tag` → `TRUE` (walk as a `tag` wire node)
- `shiny.tag.list` → `TRUE` (walk as a sibling list)
- default → `FALSE` (raw passthrough — plain lists, numbers, and `character` vectors, including `HTML()` whose class vector is `c("html", "character")`)

The `as.tags`-able test is intentionally NOT used: `as.tags.list` and `as.tags.character` exist in htmltools, so a dispatch-based "does `as.tags` have a method?" check would incorrectly walk raw data payloads. The S3 generic approach keeps the opt-in surface explicit: downstream packages that want their class walked can add a `should_walk.theirclass <- function(x) TRUE` method. This mirrors Python's `_should_walk` (which checks `isinstance(value, (Node, Tag, TagList))` and returns `False` for `str`/`bytes`/plain scalars). Returned payload has `unbox()`-wrapped scalars, so Shiny's serializer emits scalar `name`/`value`/`type`.

## Error handling

- `node()`: `cli::cli_abort` on non-scalar/empty `type` or unnamed `props`.
- Walker: unknown object → `htmltools::as.tags(x)`; if that errors, the error surfaces (clear htmltools message). No silent drops except documented `NULL`/dependency/metadata cases.
- `render_reactive`: `cli::cli_warn` (not abort) on harvested deps — parity with Python.
- Bookmark: unchanged.

## Testing

**Unit tests:**
- `test-node.R` — constructor, validation, mixed children accepted.
- `test-wire.R` — each `as_wire` method; attr translation; number/logical→text coercion; html passthrough; dependency harvest; `NULL`; `as.tags` fallback; scalar unboxing (assert `jsonlite::toJSON` of the output has scalar `name`/`value`, empty children `[]`, empty props `{}`).
- `test-render.R` (rewritten) — node→tree, tag→tree, raw list passthrough, NULL→NULL, dep→warning; plus a `shiny::testServer` integration check asserting the **actual serialized output** has unboxed scalars.
- `test-static-mount.R` — `as.tags.shinyreact_node` emits `.shinyreact-static` + inline JSON with `<`→`<` escaping; attaches the shinyreact dep + harvested deps.

**Cross-language parity (expanded shared fixtures):**
- Replace `pkg-py/tests/fixtures/wire_format/*.json` with new tree fixtures: `react_node`, `tag_child`, `text_child`, `html_child`, `mixed_tree`, `taglist_root`.
- Rewrite `pkg-py/tests/test_wire_fixtures.py` to use the new API (`Node.to_dict()`/`serialize_ui()`), generating + asserting the fixtures (clears the merge-introduced CI failure).
- Rewrite `pkg-r/tests/testthat/test-parity.R` to build the equivalent R trees and compare semantically to the committed Python fixtures (order-insensitive where order is insignificant; `children` order significant).
- `make r-check-fixtures` keeps the R copies byte-identical to the Python source.

**`R CMD check`:** stays green; the accepted `shiny:::` bookmark note remains the only NOTE.

## Examples

Re-verify the 4 ports (`examples/app-r/{01-hello-world,02-inputs,04-messages}`, `examples/ui-tsx-r/01-hello`) build and serialize correctly under the new walker (the `node()` helpers are unchanged at the call site; only the serialization underneath changed). Optionally, one example child uses a raw `tags$...` inside a `node()` to demonstrate htmltools nesting (nice-to-have).

## Cleanup / migration

- Delete `pkg-r/R/spec.R`, `pkg-r/R/to_spec.R` and the obsolete tests (`test-spec.R`, `test-to-spec.R`, `test-wire-json.R` — reshaped into `test-wire.R`).
- Remove `S7` from `DESCRIPTION` Imports; remove `@import S7` from the package doc; re-document.
- Update `docs/features.md` R section (drop `spec`/`element`/`to_spec`; describe `node()`, htmltools nesting, static mounts).
- Update `docs/superpowers/specs/2026-05-26-r-package-design.md` to point at this rework for the data-model/wire sections.
- Resolve the merge-added "R package wire format must follow #119" todo and the stale flat-`Element`/`.wire_json` R todos in `docs/todos.md`.

## References

- Python reference: `pkg-py/src/shinyreact/_spec.py` (`_walk`, `serialize_ui`, `Node`), `_reactive_output.py` (`transform`, `_should_walk`).
- JS reference: `js/src/spec.ts` (discriminated union), `js/src/renderer.tsx` (dispatch), `seedInlineSpecs` (static mounts).
- #119 / #88, original R spec `docs/superpowers/specs/2026-05-26-r-package-design.md`.
