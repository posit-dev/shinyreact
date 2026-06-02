# Split the overloaded renderer into `render_react` + `reactive_output`

**Date:** 2026-06-02
**Status:** Approved (design)

## Problem

Today a single server-side renderer is overloaded to serve both first-class
patterns:

- **Python** `reactive_output` both walks htmltools/`Node` content into a JSON
  spec (the `app.py` pattern) *and* passes raw `Jsonifiable` data through for
  `useShinyOutputValue()` (the `ui.tsx` pattern).
- **R** `render_react` does the same double duty.

This conflates two distinct intents under one name, and the names are
inconsistent across languages (Python `ui_output` / `reactive_output` vs R
`ui_output_react` / `render_react`). It also leaves the verb mismatched: in the
`ui.tsx` pattern the function only *sends a value* — it does not render anything.

## Goal

Give each pattern its own intent-named server function, with names that match
across R and Python (`app.R` / `app.py` parity), and reserve `render_react` for
the case where the server actually describes UI to render.

## Design

### Naming (both languages)

| Pattern | UI side | Server side | Accepted input (Python type) | Default UI |
|---|---|---|---|---|
| **app.R / app.py** (describe UI as objects) | `output_react(id)` | `render_react(...)` | `TagChild` (includes `Node`) | `output_react(id)` |
| **ui.tsx** (pure reactive computation; client reads via `useShinyOutputValue`) | — | `reactive_output(...)` | `Jsonifiable` | none |

### Renames

- **R**
  - `ui_output_react` → `output_react`
  - `render_react` — unchanged name; remains the UI-rendering renderer, now
    documented as the `app.R` pattern's renderer.
  - **add** `reactive_output` — the `ui.tsx` pattern's data renderer.
- **Python**
  - `ui_output` → `output_react`
  - **add** `render_react` — takes over today's `reactive_output` UI-walking
    behavior; typed as accepting `TagChild`; `auto_output_ui()` returns
    `output_react(id)`.
  - `reactive_output` — narrowed to the data case; typed as accepting
    `Jsonifiable`; `auto_output_ui()` returns `None`.

### Type-only split (no runtime assertions)

The split is **expressed through types, not enforced at runtime**:

- **Python:** `render_react` is a `Renderer[TagChild]` (accepting `Node`),
  `reactive_output` is a `Renderer[Jsonifiable]`. Pyright flags misuse;
  **nothing raises at runtime**.
- **R:** no `stopifnot`/assertions. Two functions, documented intent only.

At runtime **both functions share the same transform**: walk `node()` / tag /
`TagChild` content into a JSON spec; pass `Jsonifiable` data through unchanged
(the existing `_should_walk` / `should_walk` logic). The HTMLDependency warning
emitted when walked content carries deps is preserved in both.

The only real runtime differences between the two functions are:

1. The Python static type surface (`TagChild` vs `Jsonifiable`).
2. The default UI: `render_react` → `output_react(id)`; `reactive_output` →
   none (Python `auto_output_ui()` returns `None`; R passes no default UI to
   `createRenderFunction`).

### Boundary notes (informational, not enforced)

- `render_react` is the home for `node()`, `Tag`, `TagList`, `Tagifiable`,
  `HTML()`, and scalar text/number children — anything in `TagChild`.
- `reactive_output` is the home for `dict`/named list, `list`, scalars, and
  `None`/`NULL` — anything `Jsonifiable`.
- **Scalars** (bare strings, numbers, `NULL`/`None`) are valid in **both**.
  Because the split is type-only, a scalar returned from either function works.
- `None`/`NULL` is accepted by both ("no value" / renders nothing / sends null).

### `auto_output_ui` for Python `reactive_output`

Returns `None` (no placeholder). A `reactive_output` used in Shiny Express
auto-output context simply places no UI — consistent with the `ui.tsx` pattern,
where the client owns all UI and reads the value through a hook.

## Migration (hard rename — no deprecated aliases)

Pre-release, so rename outright and update every call site. There are **no**
backward-compatible aliases.

### The migration rule is pattern-based

Decide per output by the pattern it serves, not solely by its return type
(scalars are valid in both, so return type alone is ambiguous):

- Output paired with an `output_react` placeholder (the `app` pattern) →
  `render_react`.
- Output with no placeholder, value consumed by a hook (the `ui.tsx` pattern) →
  `reactive_output`.

### Concrete consequences

- **Python `app-py/*` examples** using `@shinyreact.reactive_output` to return
  `Node`/spec content (e.g. `app-py/03-outputs`) → `@shinyreact.render_react`.
  Their `ui_output(...)` calls → `output_react(...)`.
- **Python `ui-tsx/*` examples** using `@reactive_output` for data passthrough
  (e.g. `ui-tsx/05-temperature`) → stay `reactive_output`.
- **R `app-r/*` examples** using `render_react` with `ui_output_react` (e.g.
  `app-r/02-inputs`) → `render_react` stays; `ui_output_react` →
  `output_react`.
- **R `ui-tsx-r/*` examples** using `render_react` for data outputs read by
  hooks (e.g. `ui-tsx-r/01-hello`) → migrate to `reactive_output`.

## Files in scope

- **Python source:** `pkg-py/src/shinyreact/_output.py` (rename `ui_output` →
  `output_react`), `pkg-py/src/shinyreact/_reactive_output.py` (split into
  `render_react` + narrowed `reactive_output`; consider renaming the module to
  `_render_react.py` or adding `_render_react.py`), `__init__.py` exports.
- **R source:** `pkg-r/R/output.R` (rename), `pkg-r/R/render.R` (add
  `reactive_output`), `NAMESPACE`, `man/*.Rd` (regenerate via roxygen),
  `_pkgdown.yml`.
- **Tests:** `pkg-py/tests/test_output.py`, `test_reactive_output.py`,
  `test_set_react_page.py`, `test_bookmark_restore.py`, the playwright fixture
  apps; `pkg-r/tests/testthat/test-ui-output.R`, `test-render.R` (+ a new test
  asserting `reactive_output` exists and passes data through with no default
  UI).
- **Examples:** all `examples/app-py/*`, `examples/ui-tsx/*`,
  `examples/app-r/*`, `examples/ui-tsx-r/*` and their `README.md`s, per the
  migration rule above.
- **Current docs:** `README.md`, `pkg-py/README.md`, `pkg-r/README.md`,
  `CLAUDE.md`, `DESIGN.md`, `docs/features.md`, `docs/app-py-vs-ui-tsx.md`,
  `docs/todos.md`, `docs/timeline.md`, `.claude/references/playwright-e2e-tests.md`.
- **Out of scope:** historical records under `docs/superpowers/specs/` and
  `docs/superpowers/plans/` and `decisions/` — these are point-in-time records
  and are not rewritten.

## Testing

- Python: existing `test_reactive_output.py` splits to cover `render_react`
  (walks UI, default UI = `output_react`, dep warning) and `reactive_output`
  (passes data through, `auto_output_ui()` returns `None`). `test_output.py`
  updated for `output_react`. Type-level expectations verified by `pyright`
  (`make py-check-types`).
- R: `test-render.R` keeps `render_react` coverage; add `reactive_output`
  coverage (data passthrough, no default UI). `test-ui-output.R` updated for
  `output_react`.
- Full suite: `make py-check`, `make r-check`, and the e2e fixtures must pass
  after the rename.
