# R Package Design — `shinyreact` (pkg-r)

> **Note (2026-05-29):** The data-model, wire-format, `to_spec()`/`Spec`/`Element` sections of this document are **superseded** by [`2026-05-29-r-wire-format-rework-design.md`](2026-05-29-r-wire-format-rework-design.md). The flat-map model (`{root, elements}`, S7 `Spec`/`Element`, `to_spec()`) was replaced by the #119 discriminated-union tree (`react`/`tag`/`text`/`html`), `node()` became a plain S3 class, and S7 was dropped. Everything else in this document (page helpers, `ui_output`, `send_message`, bookmarking, downstream extension) remains accurate.

**Issue:** [#91](https://github.com/posit-dev/shinyreact/issues/91)
**Status:** Design — awaiting implementation plan
**Related:**
- [#98](https://github.com/posit-dev/shinyreact/issues/98) (flatten wire format — R will conform to whichever format is current at PR time)
- [#27](https://github.com/posit-dev/shinyreact/issues/27) (bookmarking & initial state — Python landed this; R mirrors it in v1, see "Bookmarking")

**Baseline:** mirrors `pkg-py/src/shinyreact/` as of merge of `origin/main` (bookmarking + built-in mtime dep versioning included). The sibling Python prototypes `shinyui` / `shinyuiclassonly` are **orthogonal** — they emit traditional htmltools HTML via `tagify()` and explicitly do not touch the shinyreact wire protocol, so they do not affect this design. (They do validate the class-per-component direction this spec adopts for R via S7.)

## Goal

Promote `pkg-r/` from placeholder to a real R package mirroring the Python `shinyreact` API surface, so R Shiny users get the same two patterns the Python package ships today:

- **`app.R` pattern** — UI defined as R objects (`node()`, `spec()`, `element()`) in the Shiny app file via `page_react()`; server returns trees from `render_reactive()`.
- **`ui.tsx` pattern** — UI lives in `www/index.html` + JS; bootstrapped from R via `page_react_html()`; server is pure reactive computation, returning raw `Jsonifiable` values from `render_reactive()`.

Both patterns share a single renderer (`render_reactive`) and the same shinyreact htmlDependency (a per-output bare variant and a page-level variant that adds the bookmark restore script — see Bookmarking). The R package is pure plumbing — no UI components — same as Python.

## Non-goals (v1)

- CRAN submission and `cran-extrachecks` compliance (separate follow-up).
- `ImageOutput` / `render.plot` plumbing (separate follow-up).
- Playwright e2e against R example apps (separate follow-up).
- Switching to the nested wire format (#98 — R conforms to whichever format is current).

## Architecture

### Module layout (`pkg-r/R/`)

| File | Contents |
|---|---|
| `spec.R` | S7 classes `Spec`, `Element`, `Node`; constructors `spec()`, `element()`, `node()`; `to_spec()` S7 generic; `toJSON` S3 method dispatching on the S7 classes |
| `output.R` | `ui_output(id, extra_deps = list())` |
| `page.R` | `page_react()`, `page_bare()`, `page_react_html()`, `page_react_dep()` |
| `render.R` | `render_reactive()` — Shiny renderer that calls `to_spec()` and returns JSON for the binding |
| `message.R` | `send_message(session, type, data)` |
| `dep.R` | `shinyreact_dep()` (per-output) + `shinyreact_dep_page()` (page-level: bundle + bookmark restore script); mtime-based version |
| `bookmark.R` | `restore_script_tag()` — reads R Shiny's restore context, emits the `window.shinyreact._restore` `<script>` (mirrors Python `_restore_script_tag`) |
| `zzz.R` | `.onLoad` for `jsonlite::toJSON` S3 method registration if needed |

### Dependencies (`DESCRIPTION` `Imports`)

- `shiny` — `installExprFunction`, `createRenderFunction`, `markRenderFunction`, session machinery, restore-context access (see Bookmarking risk below)
- `htmltools` — `htmlDependency`, `attachDependencies`, `htmlTemplate`, `HTML`, `tagList`, `tags$script`, tag builders
- `S7` — classes and generic dispatch
- `jsonlite` — `toJSON` (Spec serialization + bookmark restore payload)
- `cli` — error formatting (already a transitive dep of `shiny`)
- `rlang` — only if tidy-eval helpers are needed in `render_reactive`

### Built assets

Unchanged. `inst/lib/shiny/shinyreact.{js,css}` is already populated by `make r-update-dist`. The internal `shinyreact_dep()` points at this path.

The dep **version is the bundle's mtime in whole seconds** (`file.mtime(...) |> as.integer() |> as.character()`), falling back to `as.character(utils::packageVersion("shinyreact"))` when the bundle is missing in a partially-built checkout. (R's `packageVersion()` gives a real installed version, unlike Python's hardcoded `"0.1.0"` fallback — no magic string.) This matches Python's `_dep()` after the `origin/main` merge — mtime versioning is now built into the package itself (not just examples), so browsers re-fetch after a `make update-dist`. The JS consumption side of bookmarking (`applyRestoredValues`) already ships in this shared bundle; R only emits the server-side restore script.

### Build / check wiring

Already wired in `Makefile` (`r-update-dist`, `r-check`, `r-document`, `r-format`, `r-docs-render`). No Makefile changes needed for the package itself.

## Naming conventions

- **Functions:** snake_case throughout (`ui_output`, `page_react`, `page_react_html`, `send_message`, `render_reactive`). Tidyverse-aligned. Departs from Shiny's classic camelCase by design — this isn't Shiny's package. Python's `set_react_page()` becomes `page_react_html()` in R — Python's name was a Shiny-Express artifact; R Shiny has no Express, and `page_react_html()` pairs cleanly with `page_react()`.
- **S7 classes:** PascalCase (`Spec`, `Element`, `Node`) per S7 convention. User-facing constructors are snake_case (`spec()`, `element()`, `node()`); class names only appear in `is(x, "Spec")` / S7 dispatch.

## Public API surface

### Data model

```r
# S7 classes: Spec, Element, Node (PascalCase, in NAMESPACE for dispatch)
# snake_case constructors return S7 objects of those classes.

element(type, props = list(), children = list())
# → Element with @type (chr), @props (named list), @children (list of element keys)

spec(root, elements)
# → Spec with @root (chr key), @elements (named list of Element)
#   Validator: root must be in names(elements). Mirrors Python __post_init__.

node(type, ..., props = list())
# → Node with @type, @props, @children (children = `...`, must be Nodes — see below)
# `to_spec(node())` flattens to a Spec with auto-generated keys ("auto_001", ...)

# Generic + S3 bridge
to_spec(x)                  # S7 generic — downstream registers methods on their classes
toJSON.shinyreact::Spec     # S3 method calling jsonlite via to_spec(x) first
```

#### Children rules (validated at construction)

- `Element$children` is a `list` of length-1 character vectors (element keys into the flat `elements` map). Confirmed against `pkg-py/src/shinyreact/_spec.py`.
- `Node$children` is a `list` whose every entry is a `Node` — no strings, no numbers, no `NULL`. Mirrors Python's `list[Node]` and the JS renderer (`js/src/renderer.tsx:13-22`), which only walks string keys in `children`. Primitive content (text labels, numbers) is passed via `props` and the registered React component renders it.

### UI / page helpers

```r
ui_output(id, extra_deps = list())
# → htmltools tag <div id class="shinyreact-output"> with the per-output dep
#   (shinyreact_dep()) + extra_deps attached via attachDependencies().
#   Per-output consumers do NOT carry the page-level bookmark restore script.

page_react(..., title = NULL, lang = "en")
# → full HTML page with <div id="root"></div> + the PAGE-level dep
#   (shinyreact_dep_page(): bundle + bookmark restore <script>).
#   `...` forwarded to htmltools::tags$head() for extra <head> content.

page_bare(...)
# → minimal HTML scaffold without #root.

page_react_html(path = "www/index.html")
# → reads the file, wraps via htmltools::HTML, attaches the PAGE-level dep
#   (shinyreact_dep_page()). Defaults match Shiny's documented "HTML UI"
#   convention; usable as:
#     shinyApp(ui = page_react_html(), server = function(input, output, session) { ... })
#   Works with plain HTML files (no {{ headContent() }} template syntax required).

page_react_dep()
# → htmltools::htmlDependency() for a downstream package's own JS/CSS bundle
#   (distinct from the internal shinyreact_dep()); mtime-versioned. Mirrors
#   Python's page_react_dep().
```

The page-level dep (`shinyreact_dep_page()`) is the bundle dep plus the bookmark restore `<script>` when a restore context is active; per-output `ui_output()` uses the bare bundle dep. This mirrors Python's `_dep()` vs `_dep_page()` split after the `origin/main` merge.

### Renderer

```r
render_reactive(expr, env = parent.frame(), quoted = FALSE)
# Built via shiny::installExprFunction + shiny::createRenderFunction.
# Value-transform:
#   if (is.null(value)) return(NULL)
#   payload <- to_spec(value)   # S7 dispatch; raw lists pass through identity.
#   return(payload)             # JSON-ifiable list for the output binding.
# No htmlDependency extraction at render time (matches current Python behavior).
# Deps are declared at the UI site via ui_output(id, extra_deps = list(...)).
#
# Output path note: render_reactive() returns the plain list from to_spec() and
# lets Shiny serialize it via its standard jsonlite call. toJSON / .wire_json() is
# NOT on the output critical path — those helpers are used for the bookmark payload
# and for cross-language parity tests only.
```

### Server-to-client messaging

```r
send_message(session, type, data)
# → session$sendCustomMessage("shinyReactMessage", list(type = type, data = data))
# Mirrors Python's send_message signature exactly.
# Guards: inherits(session, "ShinySession") before forwarding.
```

## Wire format (current, flat-map)

Matches Python with **semantic JSON equality** (parse both, compare structures; element-map key order is insignificant). Python `json.dumps` and R `jsonlite` differ in whitespace by design, so parity is verified by parsing and comparing the resulting structures, not by byte comparison. Subject to change when [#98](https://github.com/posit-dev/shinyreact/issues/98) lands (nested children); R conforms to whichever format is current at PR time.

```json
{
  "root": "auto_001",
  "elements": {
    "auto_001": {
      "type": "Card",
      "props": { "title": "Hello" },
      "children": ["auto_002"]
    },
    "auto_002": {
      "type": "TextInput",
      "props": { "input_id": "name", "label": "Name" },
      "children": []
    }
  }
}
```

- `root` is a string key into `elements`.
- `elements` is an object keyed by string. Keys are opaque (`auto_001`, `auto_002`, ... when auto-generated by `to_spec(node())`; arbitrary strings when constructed via `spec()` directly). **Keys are not Shiny input/output IDs** — those live in `props` as `input_id` / `output_id`.
- Each element has `type` (chr), `props` (object, may be empty), `children` (array of string keys — may be empty array, never `null`).
- Auto-key generation: left-to-right depth-first, zero-padded to 3 digits, prefix `auto_`. Matches Python.

## Bookmarking (issue #27)

Python ships bookmark restore for shinyreact: when a page loads with a bookmark query string, the server injects a `<script>` into the page head carrying the restored input values, and the shared JS bundle seeds them into the input registry **before** Shiny connects. R mirrors the **server half**; the JS half is already in the shared bundle.

### Flow

1. **JS (shared bundle — no R work):** `applyRestoredValues(registry)` (`js/src/shiny-react/bookmark.ts`) reads `window.shinyreact._restore`, seeds each entry into the input registry via `add()` (stored without sending to Shiny), then replaces the global with an applied-sentinel. Idempotent.
2. **R (`bookmark.R` — `restore_script_tag()`):** reads R Shiny's active restore context for the loading request; if present and non-empty, emits a head `<script>` setting `window.shinyreact._restore = JSON.parse(<js-string-literal>)`. Returns `NULL` when there is no restore context or it is empty.
3. **Wiring:** `shinyreact_dep_page()` = bundle dep + `restore_script_tag()` (when non-`NULL`). `page_react()` and `page_react_html()` use the page-level dep; `ui_output()` uses the bare bundle dep.

### Payload encoding (must match Python `_restore_script_tag` exactly)

```js
window.shinyreact = window.shinyreact || {};
window.shinyreact._restore = JSON.parse(<js-string-literal>);
```

- Serialize the value map with `jsonlite::toJSON(values, auto_unbox = TRUE)`, then replace `</` with `<\/` (prevents premature `</script>` close).
- Wrap that JSON text as a JS string literal via a second `toJSON()` pass (double-encode) so `\n` / quotes survive the JS parser before `JSON.parse` runs.
- Emit non-ASCII (including U+2028 / U+2029) as `\uXXXX` escapes. `jsonlite::toJSON` does this when configured; verify the byte output matches Python's `json.dumps(ensure_ascii=True)` in the cross-language fixture test.
- The `JSON.parse(...)` wrapper (vs. a bare object literal) is required so keys like `__proto__` / `constructor` become ordinary data properties — same reason as Python.

### Security (carry Python's warning verbatim into R docs)

Bookmarked input values appear in the rendered page source. In URL bookmark mode they are already in the URL; in server-stored mode (`?_state_id_=...`) this script re-exposes them in the page source. Anything that can read the HTML can read these values. Apps must not bookmark credentials, tokens, or PII.

### Known v1 limitation: `auto_unbox` shape mismatch

R's `jsonlite::toJSON(auto_unbox = TRUE)` serializes a length-1 R vector as a JSON scalar (`"a"`), while Python's `json.dumps` emits a JSON array (`["a"]`). For multi-value inputs (e.g. checkbox-groups) where the user has selected exactly one option, R restore payloads seed a scalar into the JS input registry instead of the expected single-element array, which can produce type mismatches. This is a known v1 limitation tracked in [#27](https://github.com/posit-dev/shinyreact/issues/27).

### Restore-context API access — use `shiny:::` internals (decided)

Python reads the restore context via a **private** module (`shiny.bookmark._restore_state.get_current_restore_context`) and `ctx.input.as_dict()` directly, deliberately avoiding `restore_input()` (which marks values used). R mirrors this with R Shiny's internal restore-context API — **`shiny:::` access is accepted** (decided, not a spike).

Requirements for the R implementation:

- Locate R Shiny's restore context for the current request via its internal API (e.g. `shiny:::RestoreContext` / the restore context hung off the current reactive domain).
- Read the full restored input map **without** consuming/marking values, so the app's own `restoreInput()` calls still work — the non-destructive read is the same constraint Python honors by reading `ctx.input.as_dict()` rather than `restore_input()`.
- Cover both bookmark modes (URL and server-stored `?_state_id_=...`); using internals means we are not limited to reconstructing the map from the query string.

Because this depends on Shiny internals, **pin a `shiny` version floor in `DESCRIPTION`** and isolate every `shiny:::` call in `bookmark.R` behind a thin wrapper (one function) so a future Shiny API change is a single-site fix. Add a brief comment at each `:::` site explaining why the internal is used and which public API would replace it if one appears.

## Downstream extension pattern

A downstream package (e.g. the R analog of `shinyshadcn`) provides:

1. **JS bundle** that calls `window.shinyreact.registerComponents(catalog, registry)` at load — same contract as Python downstream packages, unchanged.
2. **`htmlDependency`** for its JS+CSS bundle, attached at the UI site via `ui_output(id, extra_deps = list(my_pkg_dep()))`. The package may export `my_pkg::ui_output(id)` and `my_pkg::page_react(...)` wrappers that inject the dep automatically.
3. **S7 classes for component types**, with `to_spec` methods:

```r
Card <- S7::new_class("Card",
  properties = list(
    title    = S7::class_character,
    children = S7::class_list
  )
)

S7::method(to_spec, Card) <- function(x) {
  list(
    type     = "Card",
    props    = list(title = x@title),
    children = lapply(x@children, to_spec)
  )
}

# Constructor stays snake_case
card <- function(title, ...) Card(title = title, children = list(...))
```

End-user code in `app.R`:

```r
library(shinyreact)
library(shinyrshadcn)

server <- function(input, output, session) {
  output$hello <- render_reactive({
    card("Hello!",
      text_input("name", placeholder = "Your name"),
      output_display("greeting")
    )
  })
}
```

Two key properties:

- **Single rendering entry point.** Downstream packages never call `render_reactive()` themselves or wrap it. They register `to_spec` methods on their S7 classes. The S7 generic is the extension surface.
- **Raw-list escape hatch.** A user can return a plain list from `render_reactive` directly; `to_spec()`'s default method is identity for unclassed inputs.

`to_spec()` default behavior:

- **Unclassed inputs** (plain lists, vectors): identity.
- **S7 object with no registered method:** abort with a clear message naming the class.

## Error handling & validation

S7 validators run at construction (`Spec()` / `Element()` / `Node()`). Errors via `cli::cli_abort()`.

| Field | Rule |
|---|---|
| `type` | non-empty character of length 1 |
| `props` | named list (every entry has a non-empty name) or empty list |
| `Element$children` | list of length-1 character vectors |
| `Node$children` | list whose every entry is a `Node` (no strings, no numbers, no `NULL`) |
| `Spec` | `root` is length-1 character; `root %in% names(elements)` (matches Python `__post_init__`) |

Example error:

```
✖ `node()` children must be Node objects.
  Children at positions [2, 4] are <character>.
ℹ Pass text via `props` (e.g., props = list(text = "Hello")) — the registered
  React component decides how to render it.
```

**Runtime errors:**

- `render_reactive()` value-transform: if `to_spec()` hits an S7 class with no method, abort naming the class. (Plain lists pass through; only registered classes with missing methods trigger this.)
- `to_spec()` recursive errors bubble unchanged. No wrapping.
- `send_message()` validates `inherits(session, "ShinySession")` before forwarding.

**Explicitly not validated:**

- `props` *values* — arbitrary `Jsonifiable`; downstream components own the meaning.
- `htmlDependency` objects passed in `extra_deps` — `htmltools::attachDependencies()` handles its own validation.

## Testing strategy

### Unit tests (`pkg-r/tests/testthat/`)

| File | Covers |
|---|---|
| `test-spec.R` | Constructors; S7 validators reject bad inputs; `Spec` root validation; `to_spec(node())` keys + structure |
| `test-to-spec.R` | `to_spec()` identity on lists; dispatch on `Node`/`Element`/`Spec`; error on unregistered S7 class |
| `test-toJSON.R` | `jsonlite::toJSON()` on a `Spec` emits the exact wire format (scalar auto-unboxing, empty arrays as `[]`) |
| `test-ui-output.R` | `ui_output(id)` returns expected tag with `shinyreact-output` class and `shinyreact` dep; `extra_deps` merge correctly |
| `test-page.R` | `page_react()` / `page_bare()` / `page_react_html()` return valid HTML; page helpers carry the page-level dep; `page_react_html()` works on a plain HTML file with no `{{ headContent() }}` |
| `test-render.R` | `render_reactive()` wraps `createRenderFunction` correctly; `Node` → expected JSON; raw list passes through; `NULL` returns `NULL` |
| `test-send-message.R` | `send_message()` calls `session$sendCustomMessage("shinyReactMessage", ...)` with expected payload (mock session) |
| `test-bookmark.R` | `restore_script_tag()` returns `NULL` with no restore context / empty map; with a restore map, emits the exact `window.shinyreact._restore = JSON.parse(...)` script; double-encoding and `</`→`<\/` escaping correct; `__proto__`/`constructor` keys survive; non-ASCII emitted as `\uXXXX`. Byte-compare against the Python output for the same input map (cross-language fixture). |

Prefer `expect_equal()` / `expect_identical()` for small inline expectations. Reserve `testthat::expect_snapshot()` for larger outputs (full JSON of a 3-level tree) where the diff is the test's value.

### Cross-language wire-format parity

The critical guarantee: R-emitted JSON ≡ Python-emitted JSON for equivalent input trees. Two layers:

1. R snapshot/`expect_equal` tests on ~5 canonical fixtures (single element, nested 3-level tree, empty children, multiple props, empty `Spec`).
2. **Cross-language fixture check:** the same 5 fixtures live under `pkg-py/tests/fixtures/wire_format/*.json`, generated by Python via `Spec.to_dict() | json.dumps`. R reads each `.json` and asserts **semantic JSON equality** (parse both, compare structures; element-map key order is insignificant) with what R emits for the equivalent R input. Python `json.dumps` and R `jsonlite` differ in whitespace by design, so byte comparison is not used. Python's own tests assert the generator matches committed fixtures. If R and Python drift, both suites fail.

This is the strongest defense against subtle divergence (`jsonlite` auto-boxing, key ordering, empty-array shape). Python fixture commit is a prerequisite task; tracked in #91's implementation plan. The bookmark restore-script payload (`test-bookmark.R`) participates in the same cross-language fixture scheme — Python commits the expected `_restore` script for a canonical input map; R asserts semantic equality against the expected output.

### `R CMD check`

Green via `make r-check`. No `Note`s about undeclared imports or hidden globals. **`shiny:::` is used intentionally** for restore-context access (see Bookmarking) — `R CMD check` emits a Note for `:::` calls to another package; this Note is accepted and documented (pinned `shiny` floor in `DESCRIPTION`, wrapper-isolated calls). All other Notes must be resolved.

## Examples to port

| Example | Pattern | Why |
|---|---|---|
| `examples/app-r/01-hello-world/` | `app.R` | Composes `card()`/`text_input()`/`output_display()` via `node()` — exercises the whole Spec path. Direct port of `examples/app-py/01-hello-world/`. |
| `examples/app-r/02-inputs/` | `app.R` | Covers ~10 input widget types — exercises `useShinyInput` round-trip. Port of `examples/app-py/02-inputs/`. |
| `examples/app-r/04-messages/` | `app.R` | Exercises `send_message()` end-to-end. Port of `examples/app-py/04-messages/`. |
| `examples/ui-tsx-r/01-hello/` | `ui.tsx` | Exercises `page_react_html()` + raw-JSON renderer return. Port of `examples/ui-tsx/01-hello/`. |

Bookmarking is demonstrated by enabling `enableBookmarking("url")` in `02-inputs` (it doubles as the bookmark demo), plus manual browser verification (set inputs → bookmark → reload restores them).

Out of scope for v1 examples: `03-outputs` (needs `ImageOutput`), `05-shadcn` through `10-columns` (downstream-package territory or larger UI surface without new API coverage).

## Docs touchpoints

- `docs/features.md` — add R column or section mirroring the Python table; mark each row Working/Pending. Note that JS bridge hooks are accessible from R apps the same way (via the JS bundle on `window.shinyreact`).
- `README.md` — brief "R" section pointing at `examples/app-r/01-hello-world/` and `pkg-r/`.
- `pkg-r/README.md` (new) — minimal: install, hello-world snippet, link to `docs/features.md`.
- `pkg-r/_pkgdown.yml` — minimal config; site content fills in over time. `make r-docs-render` should produce a non-empty site.

## Open follow-ups (out of scope for v1)

- CRAN submission prep (separate ticket).
- `ImageOutput` / `render.plot` equivalent in R.
- Playwright e2e against R example apps.
- Migration to nested wire format when [#98](https://github.com/posit-dev/shinyreact/issues/98) lands.

## References

- Python source: `pkg-py/src/shinyreact/`
- JS renderer: `js/src/renderer.tsx`, `js/src/spec.ts`
- Shiny "HTML UI" convention: <https://shiny.posit.co/r/articles/build/html-ui/>
- Shiny `htmlTemplate` docs: <https://shiny.posit.co/r/articles/build/templates/>
- `renderUI` dep-injection pattern: [`rstudio/shiny@ab02739/R/shinywrappers.R#L768`](https://github.com/rstudio/shiny/blob/ab0273969666aedc5b6968739aafe91e14a9ded0/R/shinywrappers.R#L768)
- Issue #91 (this work)
- Issue #98 (wire-format change)
