# Split `shinyjson` into `shinyjsonold` + new SPA-first `shinyjson`

**Date:** 2026-04-28
**Status:** Approved (verbally), awaiting spec review

## Motivation

`DESIGN.md` proposes a SPA-first architecture in which the server file contains
only reactive computation, the client is an AI-generated React SPA, and the
JSON-spec transfer layer (`Spec`, `Element`, `@json-render/react`) becomes
unnecessary. This is a drastic departure from the current `shinyjson` package.
To prototype the new direction without disturbing existing users, we split the
Python package into two parallel packages:

- `shinyjsonold` — verbatim rename of today's `shinyjson` (JSON-spec model).
- `shinyjson` — new, minimal package implementing the SPA-first server-side
  primitives.

## Scope

**In scope:**

- Rename `pkg-py/src/shinyjson/` → `pkg-py/src/shinyjsonold/`.
- Update `pyproject.toml` to ship both packages from one wheel.
- Update Python tests to import `shinyjsonold`.
- Update existing examples (1–12) to import `shinyjsonold`.
- Create new `pkg-py/src/shinyjson/` with `SpaApp` and `render_json`.
- Copy the JS bundle from `shinyjsonold/www/` into the new `shinyjson/www/`
  (byte-identical for now).
- Add a new `examples/13-spa-hello/` using the new package.
- Add one-line note to `docs/STATUS.md`.

**Out of scope:**

- `pkg-r/`, the `js/` source, `Makefile` build targets, the `update-dist` flow.
- Splitting/rebranding the JS bundle. Both packages ship identical JS that
  binds `window.shinyjson`. The npm-package migration (`@posit/shiny`,
  `@posit/shiny-react`) is a future effort.
- Removing or migrating any DESIGN.md §5 disallowed primitives (`render.ui`,
  `render.text`, etc.). The new package simply does not implement them.
- Adding a build-tool wrapper (`shiny run` integration, watch mode, etc.).

## New `shinyjson` package

### Public API

```python
from shinyjson import SpaApp, render_json

@render_json
def my_data():
    return {"title": "Hello", "count": 42}

app = SpaApp(www_dir, server)
```

### `SpaApp`

A subclass of `shiny.App` that:

1. Reads `{www_dir}/index.html` as raw HTML.
2. Wraps it in a `TagList(HTML(...))` so Shiny still injects its own runtime
   scripts (Shiny's JS client is not yet on npm).
3. Passes `static_assets=www_dir` so the entire `www/` directory is served.
4. Forwards `**kwargs` to `shiny.App`.

This is the same code as today's `examples/10-spa-hello/spa_app.py`, lifted
into the package.

### `render_json`

A `Renderer[Jsonifiable]` subclass whose `transform` passes the value through
unchanged. No `Spec` handling, no `extra_deps` extension hook (Tenet 4: no
dynamic dependency injection).

### HTMLDependency

The new `shinyjson.ui` is **not** part of the public API in this iteration —
SPA-first apps do not call any UI factory; the HTMLDependency is attached
internally by `SpaApp` so the bridge JS loads. The dependency `name` is
`shinyjson`, version pinned to the package version, source pointing at the
package's `www/` directory.

## `shinyjsonold` package

Pure rename — no behavior changes. Every internal `import shinyjson` is
rewritten to `import shinyjsonold`, and the HTMLDependency's `name` field is
changed to `shinyjsonold` so it does not collide with the new package's
dependency if (hypothetically) both were loaded together. The CSS class
`shinyjson-output` and the JS `window.shinyjson` global are unchanged — old
and new apps never run on the same page, and rebranding them now adds risk
without benefit.

## Tests and examples

- `pkg-py/tests/` — every `import shinyjson` becomes `import shinyjsonold`.
  Snapshots regenerated if necessary.
- `examples/1-hello-world` ... `examples/12-columns-spa` — every
  `import shinyjson` becomes `import shinyjsonold`. No other changes.
- `examples/13-spa-hello/` — clone of `examples/10-spa-hello/` with:
  - `app.py` imports the new `shinyjson`, uses `SpaApp` from the package
    (local `spa_app.py` is removed), and uses `@shinyjson.render_json`.
  - `App.jsx` is unchanged.

## `pyproject.toml`

The hatchling configuration currently points at `pkg-py/src/shinyjson` as the
single package. After this change it must declare both
`pkg-py/src/shinyjson` and `pkg-py/src/shinyjsonold` as packages so they ship
together from one wheel.

## Acceptance criteria

- `make py-check` passes.
- `examples/13-spa-hello` runs (`uv run shiny run examples/13-spa-hello/app.py`)
  and shows the same behavior as today's `examples/10-spa-hello`.
- Existing `examples/10-spa-hello` (now importing `shinyjsonold`) still runs.
- `docs/STATUS.md` mentions both packages.
