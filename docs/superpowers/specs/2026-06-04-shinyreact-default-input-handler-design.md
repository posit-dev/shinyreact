# Default input handler — clean array-of-records on the R server

**Date:** 2026-06-04
**Status:** Proposal — pending implementation plan
**Resolves:** #124

## Summary

`useShinyInput` values sent as an **array of objects** (e.g. a file input sending
`[{name, size, type}, ...]`) arrive on the R server as a **flat named atomic
vector** — keys repeating once per element — instead of a list of records. Python
gives a clean list of dicts; R diverges, and the natural port
(`for (f in input$x) f$size`) fails with `$ operator is invalid for atomic vectors`.

This spec makes shinyreact route every untyped `useShinyInput`/`useSetShinyInput`
value through a built-in input handler, `shinyreact.default`, registered in both R
and Python. Zero config: existing JS components are unchanged. In R the handler
preserves arrays-of-objects as a list of records while still flattening
arrays-of-scalars to atomic vectors (matching Shiny's existing default); in Python
it is a no-op. A second handler, `shinyreact.asis`, is also shipped as an explicit
opt-in escape hatch that returns the parsed value completely untouched.

## Context

### Why R flattens (verified against shiny 1.13.0)

R Shiny decodes inbound messages with `safeFromJSON(..., simplifyVector = FALSE)`,
so `[{name,size,type}, ...]` parses to a clean
`list(list(name=, size=, type=), ...)` — identical in shape to Python's list of
dicts. The flattening happens **afterward**, in Shiny's *default* (no-`type`) input
handler (`shiny:::applyInputHandler`):

```r
else if (is.list(val) && is.null(names(val))) {
    return(unlist(val, recursive = TRUE))   # <- flattens the records
}
else {
    return(val)
}
```

A `:type` suffix on the input id intercepts **before** that branch — the handler
receives the clean parsed structure. So the fix is a server-side input handler, not
a client change. (The wire-level `:type` mechanism already exists from #97; see
`docs/superpowers/specs/2026-05-13-input-handler-type-design.md`.)

### Why a single pure-identity handler is not enough

`unlist` does double duty: it flattens object arrays (the bug) **and** flattens
scalar arrays such as `[0, 100]` (range slider) or `["a", "b"]` (multi-select) into
idiomatic atomic vectors (`c(0, 100)`, `c("a", "b")`) — which is what R authors
expect (`input$range[2]` is `100`, not a one-element list). Because
`shinyreact.default` becomes the *global* default, it sits in front of scalar
arrays too. A pure `return(value)` handler would regress them to unnamed lists.
Python's deserializer never simplifies, so its handler can be pure identity.

Verified behavior (shiny 1.13.0, `simplifyVector = FALSE`):

| JS sends | Shiny default `unlist` (today) | `shinyreact.default` (R) | `shinyreact.asis` (R) |
| --- | --- | --- | --- |
| `[0, 100]` | `c(0, 100)` | `c(0, 100)` | `list(0, 100)` |
| `["a", "b"]` | `c("a", "b")` | `c("a", "b")` | `list("a", "b")` |
| `[{name,size}, …]` | flat named vector (**bug**) | list of records | list of records |
| scalar `5` | `5` | `5` | `5` |
| single object `{a:1}` | `list(a=1)` | `list(a=1)` | `list(a=1)` |
| `[]` | `NULL` | `NULL` | `list()` |
| `[[1,2],[3,4]]` | `c(1,2,3,4)` | `c(1,2,3,4)` | `list(list(1,2), list(3,4))` |

`shinyreact.default`'s **only** behavioral difference from Shiny's current default is
the array-of-objects row — the exact bug. `shinyreact.asis` returns the parsed value
completely untouched (the escape hatch for nested structures the default would
flatten).

## Design

### Two handlers

| Handler | When | R behavior | Python behavior |
| --- | --- | --- | --- |
| `shinyreact.default` | applied automatically to every untyped input | smart (preserve records, flatten scalar arrays) | identity |
| `shinyreact.asis` | opt-in via `type="shinyreact.asis"` | pure identity (untouched) | identity |

Both are registered in both languages at package load/import. Both must exist in
Python because Python raises `ValueError: No input handler registered for type` if a
`:type` arrives without a registered handler (and R `stop()`s likewise).

### JS — default the wire suffix

`js/src/shiny-react/input-registry.ts`. `entry.type` semantics are unchanged (so the
existing first-writer-wins type-conflict logic in `updateType` is untouched); only
the *wire suffix* gains a default:

```ts
export class InputRegistryEntry<T> {
  private static readonly DEFAULT_TYPE = "shinyreact.default";
  // …
  private setShinyInputValue(value: T) {
    const wireId = `${this.id}:${this.type ?? InputRegistryEntry.DEFAULT_TYPE}`;
    getShiny()?.setInputValue?.(wireId, value, this.opts);
  }
}
```

- An explicit `type` (e.g. `shiny.datetime`, `shinyreact.asis`) wins — the default
  applies only when `type` is omitted.
- No hook API change, no new option. `useShinyInput`/`useSetShinyInput` signatures
  are unchanged.
- Read-side hooks are unaffected (they subscribe to the bare id).

### R — register both handlers in `.onLoad`

New file `pkg-r/R/zzz.R`:

```r
.onLoad <- function(libname, pkgname) {
  shiny::registerInputHandler(
    "shinyreact.default",
    function(value, session, name) {
      is_records <- is.list(value) && is.null(names(value)) &&
        length(value) > 0 &&
        all(vapply(
          value,
          function(el) is.list(el) && !is.null(names(el)),
          logical(1)
        ))
      if (is_records) {
        return(value)
      }
      if (is.list(value) && is.null(names(value))) {
        return(unlist(value, recursive = TRUE))
      }
      value
    },
    force = TRUE
  )

  shiny::registerInputHandler(
    "shinyreact.asis",
    function(value, session, name) value,
    force = TRUE
  )
}
```

`force = TRUE` keeps registration idempotent across `devtools::load_all()` reloads.
Handler signature is `function(value, shinysession, name)` per
`shiny:::applyInputHandler`.

### Python — register both at import

New file `pkg-py/src/shinyreact/_input_handler.py`:

```python
from __future__ import annotations

from typing import Any

from shiny.input_handler import input_handlers
from shiny.module import ResolvedId
from shiny.session import Session


@input_handlers.add("shinyreact.default", force=True)
def _(value: Any, name: ResolvedId, session: Session) -> Any:
    return value


@input_handlers.add("shinyreact.asis", force=True)
def _(value: Any, name: ResolvedId, session: Session) -> Any:
    return value
```

`__init__.py` imports it for its registration side effect:

```python
from . import _input_handler as _input_handler  # noqa: F401  (registers input handlers)
```

`force=True` makes re-import idempotent.

## Example

`examples/app-r/02-inputs`:

- **No JS change** — the file input is covered by the default; this *is* the
  demonstration that zero-config works.
- `app.R` `output$fileout`: delete the `field()`-by-name reshaping workaround
  (added in PR #121) and iterate the clean structure:

  ```r
  output$fileout <- reactive_output({
    files <- input$filein
    if (is.null(files) || length(files) == 0) {
      return(NULL)
    }
    summaries <- vapply(files, function(f) {
      size_kb <- round(as.numeric(f$size) / 1024, 1)
      type_str <- if (nzchar(f$type)) f$type else "unknown type"
      paste0(f$name, " (", size_kb, " KB, ", type_str, ")")
    }, character(1))
    paste(summaries, collapse = "\n")
  })
  ```

  This mirrors the Python example's `for f in input.filein(): f["size"]` line for
  line, and only works with the handler registered (the regression demo).

## Tests

### R — testthat (`pkg-r/tests/testthat/`)

A new test file exercising both registered handlers directly (call them via
`shiny:::inputHandlers$get("shinyreact.default")` or by reconstructing the closure):

1. `shinyreact.default` and `shinyreact.asis` are both registered after the package
   loads.
2. `shinyreact.default`: array-of-objects → unchanged list of records; `[0,100]` →
   `c(0,100)`; `["a","b"]` → `c("a","b")`; scalar → unchanged; single object →
   unchanged named list; `[]`/`list()` → `NULL`; nested array `list(list(1,2),...)`
   → flattened (matches Shiny default).
3. `shinyreact.asis`: every input returned untouched — `[0,100]` stays
   `list(0,100)`; records stay a list of records; nested stays nested.

### Python — pytest (`pkg-py/tests/`)

1. Both `shinyreact.default` and `shinyreact.asis` are present in
   `shiny.input_handler.input_handlers` after `import shinyreact`.
2. Each returns its `value` argument unchanged (list of dicts, list of scalars,
   scalar, empty list).
3. Re-importing / re-registering with `force=True` does not raise.

### JS — vitest

- **Update** the ~10 assertions in
  `js/src/shiny-react/__tests__/input-registry.test.ts` that assert the bare wire id
  `"test"` to expect `"test:shinyreact.default"`, and the "no suffix when type
  omitted" case in `use-shiny-input-type.test.tsx`.
- **Add**: explicit `type` still overrides the default
  (`type="shinyreact.asis"` → wire id `"foo:shinyreact.asis"`; `type` omitted → wire
  id `"foo:shinyreact.default"`).

## Docs

- `CLAUDE.md` — under "Common patterns", a subsection: arrays of records arrive
  clean on R automatically (zero config) because shinyreact routes untyped inputs
  through `shinyreact.default`; note `type="shinyreact.asis"` as the escape hatch
  that returns the parsed value untouched.
- `docs/features.md` — note the built-in `shinyreact.default` (auto) and
  `shinyreact.asis` (opt-in) handlers.
- `docs/todos.md` — resolve/trim the related "Python-side input handlers for
  useShinyInput values" item and the array-of-objects note.
- R: roxygen/package docs as needed for the new behavior.

## Non-goals

- **data.frame coercion.** R yields a list of named lists matching Python's list of
  dicts; converting to a data.frame is opinionated and lossy for ragged/heterogeneous
  records.
- **An opt-out to a bare / no-suffix wire id.** `shinyreact.asis` already covers
  "give it to me untouched," and `shinyreact.default` equals Shiny's default for
  every shape except the bug.
- **New hook API / options.** The default is purely a wire-level concern; the
  existing `type=` option (from #97) is the override.
- **Unifying scalar-array shapes across languages.** R gives an atomic vector,
  Python gives a list — both idiomatic; this is pre-existing and intentionally
  unchanged.

## Consequences / risks

- **Version coupling.** Every shinyreact input now ships `id:shinyreact.default` on
  the wire, so the server package *must* have the handler registered or untyped
  inputs crash ("No handler registered for type"). shinyreact's JS bundle and its
  R/Python handlers ship together (committed `js/dist/`, bundled `pkg-py/.../www/`
  and `pkg-r/inst/lib/shiny/`, built via `make update-dist`), so this is controlled;
  registration must be load-time and unconditional.
- **Test churn.** The JS wire-id assertions above must be updated in lockstep with
  the implementation change.

## Files touched

```
js/src/shiny-react/input-registry.ts                 # DEFAULT_TYPE + suffix at wire call
js/src/shiny-react/__tests__/input-registry.test.ts  # update bare-id assertions
js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx  # update + add default/override cases
pkg-r/R/zzz.R                                         # NEW .onLoad registering both handlers
pkg-r/tests/testthat/test-input-handler.R            # NEW testthat suite
pkg-py/src/shinyreact/_input_handler.py              # NEW both handlers
pkg-py/src/shinyreact/__init__.py                    # import _input_handler for side effect
pkg-py/tests/test_input_handler.py                   # NEW pytest suite
examples/app-r/02-inputs/app.R                        # simplify output$fileout
docs/features.md                                      # note both handlers
docs/todos.md                                         # resolve related TODO
CLAUDE.md                                             # "Common patterns" subsection
```
```
make update-dist   # after the JS change, rebuild + copy bundles to pkg-py/ and pkg-r/
```
