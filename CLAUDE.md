# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`shinyreact` is a monorepo providing Shiny UI infrastructure for JSON-driven React rendering. It provides zero UI components — it is pure plumbing for downstream packages (e.g. `shinyshadcn`) to build on top of.

Two first-class patterns ship from this repo: the **`app.py` pattern** (`page_react` + `render_react`, server describes UI as a JSON spec built from Python/R objects in the Shiny app file) and the **`ui.tsx` pattern** (`set_react_page` + a React client whose entry conventionally lives in `ui.tsx`, server contains only reactive computation). See `DESIGN.md` and `docs/app-py-vs-ui-tsx.md` for context.

## Terminology — canonical pair

Use **`app.py`** (or **`app.py`/`app.R`** when cross-language matters) and **`ui.tsx`** consistently. **Never write "SPA", "Single Page App", "Single-Page Application", "traditional pattern", `client-ui`, or `ui-object`** in new content (docs, comments, commit messages, PR/issue text).

- **`app.py` pattern** — UI defined as Python or R objects in the Shiny app file (`app.py` / `app.R`) via `page_react()`, `Node`, etc.
- **`ui.tsx` pattern** — UI defined in a client-side codebase whose entry is conventionally `ui.tsx` (or `App.jsx`, or `app.js` for no-build); bootstrapped from the app file via `set_react_page()`. `ui.tsx` is the *idiomatic* canonical name — examples may use simpler variants like `www/app.js` (no-build) or `src/App.jsx` (Vite + JSX). Treat `ui.tsx` as a *role label* for the React entry, not a strict filename requirement.

Naming inspired by [Shiny's "Build your entire UI with HTML"](https://shiny.posit.co/r/articles/build/html-ui/) (UI object vs HTML UI), reframed around the canonical entry filenames the team actually edits.

The phrase "traditional Shiny" is fine when it refers to vanilla Shiny (no shinyreact involved). Do not use "traditional" as a label for one of `shinyreact`'s patterns.

## Repo structure

```
js/                         # TypeScript/React Vite IIFE bundle
  src/                      # index.ts, registry.ts, renderer.tsx, shiny.d.ts, shinyreact.css
  dist/                     # Built assets (committed to repo)
  src/shiny-react/          # Vendored @posit/shiny-react source
pkg-py/                     # Python package
  src/shinyreact/           # Core JSON-spec / React-bridge package
    www/                    # Bundled JS
  tests/                    # pytest tests
pkg-r/                      # R package — mirrors the Python API in R
  R/                         # node.R, output.R, render.R, page.R, wire.R, message.R, bookmark.R, dep.R
  inst/lib/shiny/            # Bundled JS (R counterpart of pkg-py www/)
  tests/testthat/            # testthat tests (incl. wire-format fixtures shared with Python)
examples/
  app-py/                   # app.py pattern examples (01-hello-world … 10-columns)
  ui-tsx/                   # ui.tsx pattern examples (01-hello … 07-plotly)
docs/                       # app-py-vs-ui-tsx.md, posit-conf-2026-goals.md
decisions/                  # Architecture decision records
pyproject.toml              # Root-level, hatchling backend
Makefile                    # All build/check/format commands
```

## Commands

```bash
# Initial setup
uv sync --all-extras --all-groups   # Python env
make js-setup                        # JS deps (cd js && npm install)
pre-commit install                   # Pre-commit hooks

# Build
make js-build                        # Build JS bundle (js/dist/)
make update-dist                     # Build JS + copy to pkg-py/www/ and pkg-r/inst/lib/shiny/

# Python checks (run all before committing)
make py-check                        # format check + type check + tests
make py-check-tests                  # pytest only
make py-check-types                  # pyright only
make py-format                       # ruff fix + format
make py-check-tox                    # full matrix: Python 3.10–3.14

# JS checks
make js-lint                         # tsc --noEmit
make js-build-watch                  # watch mode

# R checks
make r-check                         # format + tests + R CMD Check
make r-format                        # air format

# Run a single Python test
uv run pytest pkg-py/tests/test_spec.py::test_name

# Update test snapshots
make py-update-snaps
```

Run `make help` to see all targets.

## Architecture

### JS bundle

The JS output (`js/dist/shinyreact.js`) is a self-contained IIFE that bundles React 19 and vendored `@posit/shiny-react`. It registers a Shiny `OutputBinding` that finds `.shinyreact-output` elements and renders JSON specs as React component trees using an in-house recursive walker (`js/src/renderer.tsx` + `js/src/spec.ts`).

**Global API exposed at `window.shinyreact`:**
- `registerComponents(catalog, registry)` — downstream packages call this at page load to register their React components
- `useShinyInput`, `useShinyInputValue`, `useSetShinyInput`, `useShinyOutputValue`, `useShinyOutputStatus`, `useShinyMessageHandler`, `useShinyInitialized`, `useShinyBusy` — re-exported shiny-react hooks
- `React`, `ReactDOM` — shared instances (downstream ESM builds should externalize to these to avoid duplicate React)

### Python package

- `shinyreact.output_react(id, extra_deps=[...])` — creates `<div id="{id}" class="shinyreact-output">` with the shinyreact HTMLDependency (the placeholder `render_react` renders into)
- `shinyreact.page_react(...)` — full-page React app with `#root` + the shinyreact HTMLDependency
- `@shinyreact.render_react` — `Renderer[Node | TagChild]` subclass (app.py pattern); walks `Node`/htmltools content into the JSON wire tree, rendered into a matching `output_react()` placeholder. `auto_output_ui()` returns `output_react(id)`
- `@shinyreact.reactive_output` — `Renderer[Jsonifiable]` subclass (ui.tsx pattern); passes raw JSON data through for `useShinyOutputValue()` hooks, with no placeholder (`auto_output_ui()` returns `None`)
- `shinyreact.Node(type, props, children)` — the nested-tree authoring API for the app.py pattern; `children` may mix nested `Node`s, htmltools content, and scalars. The walker turns it into the JSON wire tree (`{"type": "react", "name", "props", "children"}`, plus `tag`/`text`/`html` nodes). `.serialize()` → `(wire_tree, deps)`; `.to_dict()` → wire tree (discards harvested `HTMLDependency`); `.tagify()` → a static `.shinyreact-static` mount for embedding in page chrome
- `shinyreact.send_message(session, type, data)` — sends `shinyReactMessage` custom messages consumed by `useShinyMessageHandler()`
- `shinyreact.set_react_page(path="www/index.html")` — Express helper that serves a static `www/index.html` (the ui.tsx pattern); auto-discovers `HTMLDependency` objects from traditional Shiny renderers and injects the shinyreact dep
- `shinyreact.page_react_html(path="www/index.html")` — Core-mode helper that serves a static `www/index.html` (the ui.tsx pattern) as the `ui` argument of `App(ui=..., server=...)`; attaches the shinyreact dep. The Core counterpart to the Express-only `set_react_page()`

### R package

The R package (`pkg-r/`) mirrors the Python API in R idioms; exports are `node`, `output_react`, `render_react`, `reactive_output`, `page_react`, `page_bare`, `page_react_html`, `page_react_dep`, `send_message`. Key shape differences from Python:

- `node(type, ..., props = list())` — children are the `...` args (vs Python's `children` list); produces the same JSON wire tree. Serialize via `as_wire()` / `serialize_ui()` (see `pkg-r/R/wire.R`).
- `render_react(expr, ...)` / `reactive_output(expr, ...)` are **functions** assigned to `output$id`, not decorator/`Renderer` classes.
- `page_react_html(path = "www/index.html")` matches Python's `page_react_html()` (Core-mode ui.tsx entry); Python additionally has the Express-only `set_react_page()`.
- `output_react(id, extra_deps = list())` and `send_message(session, type, data)` match Python.

The wire format is identical across languages — `make r-check-fixtures` verifies R's output matches Python's shared fixtures.

### Downstream package pattern

Downstream packages (e.g. `shinyshadcn`) extend shinyreact by:

1. **JS:** own IIFE bundle that calls `window.shinyreact.registerComponents(catalog, registry)` at load time
2. **Python UI:** `shinyreact.output_react(id, extra_deps=[my_dep()])`
3. **Python render subclass:**
   ```python
   class render(shinyreact.render_react):
       async def transform(self, value: MyComponent) -> Any:
           # Convert your component into a shinyreact.Node, then the wire dict
           return value.to_node().to_dict()
   ```
   Inject the package's `HTMLDependency` on the UI side via `shinyreact.output_react(id, extra_deps=[...])` (step 2) — `render_react` does not read an `extra_deps` class attribute.

### Built assets

`js/dist/` and `pkg-py/src/shinyreact/www/` are both committed to the repo. After changing JS source, run `make update-dist` to rebuild and copy. `pkg-r/inst/lib/shiny/` is the R counterpart (same flow).

### Build backend

`pyproject.toml` uses hatchling (not uv_build) because the package source lives at `pkg-py/src/shinyreact/` — a non-standard path that requires explicit hatchling configuration.

## Common patterns

### HTMLDependency cache-busting for examples

Shiny serves static files from `HTMLDependency` at `/lib/{name}-{version}/`. The browser caches by URL, so if the version doesn't change, edited JS files won't be picked up. In examples, use the JS file's mtime (in seconds) as the version to auto-bust the cache during development:

```python
_src_dir = Path(__file__).parent
HTMLDependency(
    name="hello-world",
    version=str(int((_src_dir / "hello_world.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "hello_world.js", "defer": ""},
)
```

This is only for examples and development. Published packages should use a fixed version.

### Action buttons

Use the Shiny action button pattern — start at `0`, increment on click:

**JS:**
```js
var [count, setCount] = useShinyInput("my_button", 0, { debounceMs: 0, priority: "event" });
function handleClick() { setCount(count + 1); }
```

`debounceMs: 0` ensures every click is delivered immediately (the default 100ms debounce can coalesce rapid clicks). `priority: "event"` marks it as an event input.

**Python:**
```python
@shinyreact.reactive_output
@reactive.event(input.my_button, ignore_init=True)
def button_response():
    return f"Clicked {input.my_button()} times"
```

`ignore_init=True` prevents firing on page load when `useShinyInput` registers the initial `0` value.

### useShinyInput defaultValue

`defaultValue` is captured on first mount only (same as `React.useState`). Inline literals like `{}` and `[]` are safe — the value is stabilized internally via `useRef`.

### useShinyMessageHandler

Inline arrow functions are safe to pass as the handler — the function is stored in a ref internally, avoiding unnecessary deregister/re-register cycles.

### Hook decomposition

The hook surface follows the Jotai/Recoil cadence — each hook has one responsibility:

| | Full | Read-only | Write-only |
|---|---|---|---|
| **Input** | `useShinyInput(id, default)` → `[value, setValue]` | `useShinyInputValue(id)` → `value` | `useSetShinyInput(id, default)` → `setValue` |
| **Output** | — (no compound) | `useShinyOutputValue(id, default?)` → `value` | — |
| **Output status** | | `useShinyOutputStatus(id)` → `"pending" \| "ready" \| "recalculating" \| "error"` | |

Pick the narrowest hook that fits the call site. A button that pushes events but never reads its own state should use `useSetShinyInput`, not `useShinyInput` with a discarded `[value]`. A display card that just reads should use `useShinyInputValue` / `useShinyOutputValue`. Narrow hooks make data-flow direction visible at the call site, prevent accidental writes from read-only components, and avoid spurious re-renders from subscribing to channels you don't observe.

### Routing input values through Shiny input handlers (`type=`)

`useShinyInput` and `useSetShinyInput` accept an optional `type` that appends `:type` to the wire id, opting into Shiny's server-side input-handler dispatch:

```js
const [when, setWhen] = useShinyInput("when", Math.floor(Date.now() / 1000), {
  type: "shiny.datetime",
});
```

```python
@reactive.effect
def _():
    print(type(input.when()))  # datetime.datetime
```

The handler name is a server-side contract: once an input id has been registered with a `type` (or with no `type`), a later mount disagreeing with that policy throws. Validation rejects empty strings, whitespace, and `:` characters at hook mount.

### Arrays of records arrive clean on R (zero config)

shinyreact routes every untyped `useShinyInput` value through a built-in
`shinyreact.default` input handler (the JS hook appends `:shinyreact.default`
to the wire id automatically). On R this means a JS component sending an array
of objects — e.g. `[{name, size, type}, ...]` — arrives as a clean list of
records, so `for (f in input$x) f$size` works just like Python's
`for f in input.x(): f["size"]`. Scalar arrays (`[0, 100]`, `["a", "b"]`) are
still flattened to atomic vectors, exactly as Shiny does by default.

If you need the parsed value returned completely untouched (e.g. a nested array
the default would flatten), opt into the pass-through handler:

```js
useShinyInput("coords", [], { type: "shinyreact.asis" });
```

Both `shinyreact.default` and `shinyreact.asis` are registered in R and Python,
so the same React component is portable across both servers.

### Avoiding flicker on input changes (use status correctly, don't conflate states)

The four output-status values exist for a reason — collapsing them into one boolean leaks DOM churn into the UI. Wrong:

```jsx
const data = useShinyOutputValue("foo");
const status = useShinyOutputStatus("foo");
const isLoading = status !== "ready";        // conflates pending + recalculating
if (!data || isLoading) return <Skeleton/>;  // unmounts the chart on every input change
```

This unmounts the populated card every time the server recomputes — destroying chart/table DOM, briefly showing a skeleton, then re-mounting fresh. Right:

```jsx
const data = useShinyOutputValue("foo");
const status = useShinyOutputStatus("foo");
if (!data) return <Skeleton/>;               // skeleton only when no data has ever arrived
return <Chart className={status === "recalculating" ? "recalculating" : ""} data={data}/>;
```

Plus a CSS rule like `.recalculating { opacity: 0.6; transition: opacity 200ms; }` so the user sees a stale-data cue without DOM tear-down. The chart node survives across input changes and React reconciles in place.

`"pending"` is the only state where you don't have data yet. `"recalculating"` means the server is computing fresh data but the previous result is still mounted — keep showing it. `"error"` is rarely surfaced today; treat like `"ready"` unless you have a use case. If your card doesn't need any of this nuance, just call `useShinyOutputValue` and skip the status entirely.

### Server pattern: fact table + shared `@reactive.calc` + per-output aggregations

Dashboards with several cards driven by the same filter input should follow:

1. **Generate or load a fact table** — long-format, one row per (date, entity) (or whatever the natural grain is).
2. **A single `@reactive.calc filtered_data`** that applies all the inputs (date, search, categories, …) to the fact table.
3. **One `@reactive_output` per card** that calls `filtered_data()` and aggregates to the shape that card needs.

This is what Shiny's reactive graph is good at: each input change recomputes `filtered_data` once and fans out to all cards. Static pre-aggregated tables that some inputs can't touch produce broken-feeling examples — the demo claims to react to a filter that visibly does nothing for half the page. See `examples/app-py/06-dashboard/data.py` for the canonical layout.

## Testing policy

When fixing a bug, add or update unit tests to cover the fix whenever possible. The test should fail without the fix and pass with it. If the fix is purely a type annotation or comment change with no runtime behavior difference, tests are not required.

- **Python tests:** `pkg-py/tests/` — run with `make py-check-tests`
- **JS tests:** `js/src/shiny-react/__tests__/` — run with `cd js && npx vitest run`
- **Playwright e2e tests:** `pkg-py/tests/playwright/` — run with `make py-test-e2e`. The `[tool.pytest.ini_options]` block ignores this subtree by default so `make py-check-tests` stays fast; `py-test-e2e` clears that with `-o addopts=`. **Adding a new e2e test:** see [`.claude/references/playwright-e2e-tests.md`](.claude/references/playwright-e2e-tests.md) for the fixture-app layout, the four traps that bit us while writing the suite, and the canonical assertion patterns.

## Open work, examples catalog

- **Open work / known issues** live in the [GitHub issue tracker](https://github.com/posit-dev/shinyreact/issues), not a checked-in TODO file. File substantive work as an issue.
- **`examples/README.md`** — the catalog of what exists today (every example, both patterns, both languages). Add a row when you add an example. The API surface itself is documented in `pkg-py/README.md` / `pkg-r/README.md` and the R pkgdown reference, not in a separate inventory.

## Key decisions

- `decisions/` contains architecture decision records. `decisions/2026-03-17-playwright-testing-architecture.md` documents the recommended approach (code-gen from TypeScript) for future browser testing — not yet implemented.
- `shiny-react` is vendored at `js/src/shiny-react/` rather than installed as an npm dependency (commit `4137071`).
- **React keys are positional by default.** The wire tree has no synthetic element-key map; React reconciles children positionally. For lists or reorderable content, pass an explicit `key` in a node's props (React reads it natively; it is not emitted as a DOM attribute). Component identity is unrelated to DOM IDs or Shiny input/output IDs — Shiny IDs are passed as component props (`input_id`, `output_id`) and are the only IDs the server tracks.
