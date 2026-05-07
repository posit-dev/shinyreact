# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`shinyreact` is a monorepo providing Shiny UI infrastructure for JSON-driven React rendering. It provides zero UI components — it is pure plumbing for downstream packages (e.g. `shinyshadcn`) to build on top of.

Two first-class patterns ship from this repo: the **`ui-object` pattern** (`page_react` + `reactive_output`, server describes UI as a JSON spec built from Python objects) and the **`client-ui` pattern** (`set_react_page` + a `www/index.tsx`-rooted React client, server contains only reactive computation). See `DESIGN.md` and `docs/client-ui-vs-ui-object.md` for context.

## Terminology — canonical pair

Use **`ui-object`** and **`client-ui`** consistently. **Never write "SPA", "Single Page App", "Single-Page Application", or "traditional pattern"** in new content (docs, comments, commit messages, PR/issue text).

- **`ui-object` pattern** — UI defined as Python or R objects in the app file (`app.py` / `app.R`) via `page_react()`, `Spec`, etc.
- **`client-ui` pattern** — UI defined in a client-side codebase (`www/`, `src/index.tsx`), bootstrapped from the app file via `set_react_page()`.

Borrowed from [Shiny's "Build your entire UI with HTML"](https://shiny.posit.co/r/articles/build/html-ui/) framing (UI object vs HTML UI) — `client-ui` is the shinyreact-flavored equivalent of "HTML UI".

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
  ui-object/                # ui-object pattern examples (01-hello-world … 10-columns)
  client-ui/                # client-ui pattern examples (01-hello … 07-plotly)
docs/                       # todos.md, features.md, client-ui-vs-ui-object.md, timeline.md
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
- `useShinyInput`, `useShinyOutput`, `useShinyMessageHandler`, `useShinyInitialized` — re-exported shiny-react hooks
- `React`, `ReactDOM` — shared instances (downstream ESM builds should externalize to these to avoid duplicate React)

### Python package

- `shinyreact.ui_output(id, extra_deps=[...])` — creates `<div id="{id}" class="shinyreact-output">` with the shinyreact HTMLDependency
- `shinyreact.page_react(...)` — full-page React app with `#root` + the shinyreact HTMLDependency
- `@shinyreact.reactive_output` — `Renderer[Spec | Jsonifiable]` subclass; converts `Spec` → dict or passes raw JSON through for `useShinyOutput()` hooks
- `shinyreact.Spec(root, elements)` / `shinyreact.Element(type, props, children)` — the data model sent to the browser (ui-object pattern)
- `shinyreact.Node` — nested tree API; `.to_spec()` auto-flattens to `Spec`
- `shinyreact.send_message(session, type, data)` — sends `shinyReactMessage` custom messages consumed by `useShinyMessageHandler()`
- `shinyreact.set_react_page(path="www/index.html")` — Express helper that serves a static `www/index.html` (the client-ui pattern); auto-discovers `HTMLDependency` objects from traditional Shiny renderers and injects the shinyreact dep

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

## Testing policy

When fixing a bug, add or update unit tests to cover the fix whenever possible. The test should fail without the fix and pass with it. If the fix is purely a type annotation or comment change with no runtime behavior difference, tests are not required.

- **Python tests:** `pkg-py/tests/` — run with `make py-check-tests`
- **JS tests:** `js/src/shiny-react/__tests__/` — run with `cd js && npx vitest run`

## docs/todos.md, features.md

These files are the primary documentation source:

- **`docs/todos.md`** — known issues and open work. Add new entries with a descriptive heading and explanation. Remove entries when fixed (no "recent fixes" log — git history is the record). Prefer a GitHub issue for substantive work and link it from here.
- **`docs/features.md`** — feature inventory for both the `ui-object` pattern and the `client-ui` pattern; JS bridge hooks; examples.
- Keep entries concise. TODOs describe the problem and constraints; feature tables describe what exists today.

## Key decisions

- `decisions/` contains architecture decision records. `decisions/2026-03-17-playwright-testing-architecture.md` documents the recommended approach (code-gen from TypeScript) for future browser testing — not yet implemented.
- `shiny-react` is vendored at `js/src/shiny-react/` rather than installed as an npm dependency (commit `4137071`).
