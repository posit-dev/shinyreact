# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`shinyjson` is a monorepo providing Shiny UI infrastructure for JSON-driven React rendering. It provides zero UI components — it is pure plumbing for downstream packages (e.g. `shinyshadcn`) to build on top of.

## Repo structure

```
js/                         # TypeScript/React Vite IIFE bundle
  src/                      # index.ts, registry.ts, renderer.tsx, shiny.d.ts, shinyjson.css
  dist/                     # Built assets (committed to repo)
  src/shiny-react/          # Vendored @posit/shiny-react source
pkg-py/                     # Python package
  src/shinyjson/            # _spec.py, _output.py, _render.py, _post_message.py, __init__.py
    www/                    # Built JS assets (copied from js/dist/)
  tests/                    # pytest tests
pkg-r/                      # R package (placeholder — not yet implemented)
docs/plans/                 # Design docs
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

The JS output (`js/dist/shinyjson.js`) is a self-contained IIFE that bundles React 19, `@json-render/react`, and vendored `@posit/shiny-react`. It registers a Shiny `OutputBinding` that finds `.shinyjson-output` elements and renders JSON specs as React component trees via `@json-render/react`.

**Global API exposed at `window.shinyjson`:**
- `registerComponents(catalog, registry)` — downstream packages call this at page load to register their React components
- `useShinyInput`, `useShinyOutput`, `useShinyMessageHandler`, `useShinyInitialized` — re-exported shiny-react hooks
- `React`, `ReactDOM` — shared instances (downstream ESM builds should externalize to these to avoid duplicate React)

### Python package

- `shinyjson.ui(id, extra_deps=[...])` — creates `<div id="{id}" class="shinyjson-output">` with the shinyjson HTMLDependency
- `@shinyjson.render` — `Renderer[Any]` subclass; converts `Spec` → dict or passes raw JSON through for `useShinyOutput()` hooks
- `shinyjson.Spec(root, elements)` / `shinyjson.Element(type, props, children)` — the data model sent to the browser
- `shinyjson.post_message(session, type, data)` — sends `shinyReactMessage` custom messages consumed by `useShinyMessageHandler()`

### Downstream package pattern

Downstream packages (e.g. `shinyshadcn`) extend shinyjson by:

1. **JS:** own IIFE bundle that calls `window.shinyjson.registerComponents(catalog, registry)` at load time
2. **Python UI:** `shinyjson.ui(id, extra_deps=[my_dep()])`
3. **Python render subclass:**
   ```python
   class render(shinyjson.render):
       extra_deps = [my_html_dependency()]
       async def transform(self, value: MyComponent) -> Any:
           return value.to_spec().to_dict()
   ```

### Built assets

`js/dist/` and `pkg-py/src/shinyjson/www/` are both committed to the repo. After changing JS source, run `make update-dist` to rebuild and copy. `pkg-r/inst/lib/shiny/` is the R counterpart (same flow).

### Build backend

`pyproject.toml` uses hatchling (not uv_build) because the package source lives at `pkg-py/src/shinyjson/` — a non-standard path that requires explicit hatchling configuration.

## Key decisions

- `decisions/` contains architecture decision records. `decisions/2026-03-17-playwright-testing-architecture.md` documents the recommended approach (code-gen from TypeScript) for future browser testing — not yet implemented.
- `shiny-react` is vendored at `js/src/shiny-react/` rather than installed as an npm dependency (commit `4137071`).
