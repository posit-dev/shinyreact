# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`shinyreact` is a monorepo providing Shiny UI infrastructure for JSON-driven React rendering. It provides zero UI components — it is pure plumbing for downstream packages (e.g. `shinyshadcn`) to build on top of.

Two first-class patterns ship from this repo: the **`app.py` pattern** (`page_react` + `reactive_output`, server describes UI as a JSON spec built from Python/R objects in the Shiny app file) and the **`ui.tsx` pattern** (`set_react_page` + a React client whose entry conventionally lives in `ui.tsx`, server contains only reactive computation). See `DESIGN.md` and `docs/app-py-vs-ui-tsx.md` for context.

## Terminology — canonical pair

Use **`app.py`** (or **`app.py`/`app.R`** when cross-language matters) and **`ui.tsx`** consistently. **Never write "SPA", "Single Page App", "Single-Page Application", "traditional pattern", `client-ui`, or `ui-object`** in new content (docs, comments, commit messages, PR/issue text).

- **`app.py` pattern** — UI defined as Python or R objects in the Shiny app file (`app.py` / `app.R`) via `page_react()`, `Spec`, etc.
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
  src/shinyreact/           # Package: set_react_page, reactive_output, page_react, Spec/Element/Node
    www/                    # Bundled JS
  tests/                    # pytest tests
pkg-r/                      # R package (placeholder — not yet implemented)
examples/
  app-py/                   # app.py pattern examples (01-hello-world … 10-columns)
  ui-tsx/                   # ui.tsx pattern examples (01-hello … 07-plotly)
docs/                       # todos.md, features.md, app-py-vs-ui-tsx.md, timeline.md
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

- `shinyreact.ui_output(id, extra_deps=[...])` — creates `<div id="{id}" class="shinyreact-output">` with the shinyreact HTMLDependency
- `shinyreact.page_react(...)` — full-page React app with `#root` + the shinyreact HTMLDependency
- `@shinyreact.reactive_output` — `Renderer[Spec | Jsonifiable]` subclass; converts `Spec` → dict or passes raw JSON through for `useShinyOutputValue()` hooks
- `shinyreact.Spec(root, elements)` / `shinyreact.Element(type, props, children)` — the data model sent to the browser (app.py pattern)
- `shinyreact.Node` — nested tree API; `.to_spec()` auto-flattens to `Spec`
- `shinyreact.send_message(session, type, data)` — sends `shinyReactMessage` custom messages consumed by `useShinyMessageHandler()`
- `shinyreact.set_react_page(path="www/index.html")` — Express helper that serves a static `www/index.html` (the ui.tsx pattern); auto-discovers `HTMLDependency` objects from traditional Shiny renderers and injects the shinyreact dep

### Downstream package pattern

Downstream packages (e.g. `shinyshadcn`) extend shinyreact by:

1. **JS:** own IIFE bundle that calls `window.shinyreact.registerComponents(catalog, registry)` at load time
2. **Python UI:** `shinyreact.ui_output(id, extra_deps=[my_dep()])`
3. **Python render subclass:**
   ```python
   class render(shinyreact.reactive_output):
       async def transform(self, value: MyComponent) -> Any:
           return value.to_spec().to_dict()
   ```
   Inject the package's `HTMLDependency` on the UI side via `shinyreact.ui_output(id, extra_deps=[...])` (step 2) — `reactive_output` does not read an `extra_deps` class attribute.

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
- **Playwright e2e tests:** `pkg-py/tests/playwright/` — run with `make py-test-e2e`. The `[tool.pytest.ini_options]` block ignores this subtree by default so `make py-check-tests` stays fast; `py-test-e2e` clears that with `-o addopts=`.

### Adding a Playwright e2e test

Tests use `pytest-playwright` + py-shiny's `create_app_fixture`. Each test gets its own spartan Shiny app booted as a subprocess. Steps:

1. **Spartan fixture app under `pkg-py/tests/playwright/apps/<name>/`:**
   - `app.py` — the smallest Shiny Express app that exercises one assertion target. Decorate one server function with whatever you're testing (`@reactive_output`, `@render.data_frame`, `@render_plotly`, …) and call `set_react_page()`.
   - **Every `app.py` MUST import something from `shiny.express`** (e.g. `from shiny.express import render`, with `# noqa: F401` if unused). Without that import, Shiny doesn't recognise the file as Express and `set_react_page()` raises `RuntimeError: No top-level recall context manager has been set`. `@render_plotly` (shinywidgets) and `@reactive_output` (shinyreact) do NOT trigger Express recognition on their own.
   - `www/index.html` — minimal bootstrap: optional `<style>` block, `<div id="root"></div>`, `<script src="app.js" defer></script>`. `shinyreact.js` is auto-injected by `set_react_page()`; do **not** add a `<script>` tag for it.
   - `www/app.js` — no-build no-JSX React. Gate render on `useShinyInitialized()`, wrap the `ShinyOutput` in `<div data-test="container">` for the direct-child assertions to bite.
   - **`set_react_page()` caches `www/index.html` at process startup** (see #82). After editing `index.html`, stop and restart the Shiny server — a browser hard-refresh alone won't help.

2. **Add a fixture line + test to `pkg-py/tests/playwright/test_shiny_output.py`:**
   ```python
   my_app = create_app_fixture("apps/<name>/app.py")  # path relative to this test file

   def test_my_thing(page: Page, my_app: ShinyAppProc) -> None:
       page.goto(my_app.url)
       ...
   ```

3. **Assertion patterns proven out by the existing suite:**
   - **No-wrapper guarantee** (the #61 / #75 regression guard): `expect(page.locator("[data-test=container] > #my_id")).to_be_attached()`. The `>` combinator fails if any wrapper sneaks back in between the container and the output.
   - **Direct-child CSS check** for the same regression, demonstrable visually: paint a hot-pink outline on direct children only (`[data-test="container"] > * { outline: 3px solid hotpink; }`) and assert `to_have_css("outline-color", "rgb(255, 105, 180)")`. A wrapper would steal the match and leave the output at its default outline. Custom elements (`<shiny-data-frame>`) default to `display: inline`; add `display: inline-block` (or `block`) on the host or the outline visually collapses onto the rendered content.
   - **Empty outputs:** use `to_be_attached()` instead of `to_be_visible()`. A `<div>` with no content has a 0×0 box and Playwright reports it "hidden".
   - **Class assertions:** order-tolerant via `to_have_class(re.compile(r"\bclass-name\b"))`. Shiny adds `shiny-bound-output` after the binding pass, so exact-string matches are brittle.
   - **`<ShinyOutput>` adds no classes of its own** — caller-supplied classes are the full set on the rendered element (plus whatever Shiny's binding adds later).

4. **CI uses Docker for the browser** via the composite action at `.github/shinyreact/setup-playwright-remote/action.yaml` (cribbed from py-shiny PRs #2208 / #2228 — avoids the ~5% chance of a 30-minute `playwright install` hang from the CDN). The `connect_options` fixture in `pkg-py/tests/playwright/conftest.py` reads `PW_TEST_CONNECT_WS_ENDPOINT` and tells pytest-playwright to `browser_type.connect()` instead of `.launch()`. Locally the env var is unset and the launch path is used unchanged — no special setup beyond `make py-install-e2e`.

## docs/todos.md, features.md

These files are the primary documentation source:

- **`docs/todos.md`** — known issues and open work. Add new entries with a descriptive heading and explanation. Remove entries when fixed (no "recent fixes" log — git history is the record). Prefer a GitHub issue for substantive work and link it from here.
- **`docs/features.md`** — feature inventory for both the `app.py` pattern and the `ui.tsx` pattern; JS bridge hooks; examples.
- Keep entries concise. TODOs describe the problem and constraints; feature tables describe what exists today.

## Key decisions

- `decisions/` contains architecture decision records. `decisions/2026-03-17-playwright-testing-architecture.md` documents the recommended approach (code-gen from TypeScript) for future browser testing — not yet implemented.
- `shiny-react` is vendored at `js/src/shiny-react/` rather than installed as an npm dependency (commit `4137071`).
