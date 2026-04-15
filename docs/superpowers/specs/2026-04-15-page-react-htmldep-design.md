# Design: HTMLDependency support for `page_react()`

## Problem

`page_react()` accepts `js_file`/`css_file` as plain string paths and emits raw `<script>`/`<link>` tags. This bypasses Shiny's HTMLDependency system, losing cache-busting, deduplication, and consistency with the rest of the shinyjson API (where `ui_output()` and `render.extra_deps` use HTMLDependency).

## Decision

- **Drop** `js_file` and `css_file` parameters from `page_react()`.
- **Add** a `page_react_dep()` convenience helper that builds an HTMLDependency from local file paths.
- **Lean on `*args`** for dependency injection — Shiny automatically hoists HTMLDependency objects from anywhere in the tag tree to `<head>`, so no separate `deps` kwarg is needed.
- `page_bare()` signature stays the same — it already accepts `*args: TagChild`, which supports HTMLDependency objects.

## API

### `page_react()` (changed)

```python
def page_react(
    *args: TagChild,
    title: str | None = None,
    lang: str = "en",
) -> Tag:
```

Always includes shinyjson's internal `_dep()` and a `<div id="root">` mount point. User-provided HTMLDependency objects passed via `*args` are hoisted to `<head>` by Shiny's rendering pipeline.

**Removed:** `js_file` and `css_file` parameters.

### `page_bare()` (unchanged)

```python
def page_bare(
    *args: TagChild,
    title: str | None = None,
    lang: str = "en",
) -> Tag:
```

No changes. HTMLDependency objects passed in `*args` are already hoisted to `<head>` automatically.

### `page_react_dep()` (new)

```python
def page_react_dep(
    *,
    js_file: str = "main.js",
    css_file: str = "main.css",
) -> HTMLDependency:
```

Convenience helper that builds an HTMLDependency from local file paths. All parameters are keyword-only (enforced by `*`).

**Behavior:**
- Resolves file paths relative to the **caller's** module directory (using `inspect.stack()` to find the caller's `__file__`).
- Uses the JS file's mtime (in seconds) as the version string for automatic cache-busting during development, matching the existing example convention documented in CLAUDE.md.
- Sets `script={"src": js_file, "type": "module"}` and `stylesheet={"href": css_file}`.
- The dependency `name` is derived from the caller's directory name (e.g., `"my-app"` for `/path/to/my-app/app.py`).
- Uses `inspect.stack()[1].filename` to locate the caller. This is the same pattern used by Shiny's own `HTMLDependency(source={"subdir": ...})` convention — it works reliably for module-level calls in app files.

### Typical usage

```python
import shinyjson

app_ui = shinyjson.page_react(
    shinyjson.page_react_dep(js_file="app.js", css_file="app.css"),
)
```

With a downstream package dependency:

```python
import shinyjson
import shinyshadcn

app_ui = shinyjson.page_react(
    shinyshadcn.dep(),
    shinyjson.page_react_dep(js_file="app.js"),
)
```

## Why `*args` instead of a `deps` kwarg

Shiny's HTMLDependency is a `MetadataNode` subclass. When the page is rendered:

1. `Tag.get_dependencies()` recursively collects all HTMLDependency objects from the entire tag tree.
2. `HTMLDocument._hoist_head_content()` injects their `<script>`/`<link>`/`<meta>` tags into `<head>`.
3. HTMLDependency objects produce no inline output where they sit in the tree.

This means an HTMLDependency passed as an `*args` child behaves identically to one placed in `<head>` explicitly. A separate `deps` kwarg would be redundant.

## Files to change

| File | Change |
|------|--------|
| `pkg-py/src/shinyjson/_page_react.py` | Remove `js_file`/`css_file` from `page_react()`. Add `page_react_dep()` function. |
| `pkg-py/src/shinyjson/__init__.py` | Export `page_react_dep`. |
| `pkg-py/tests/test_output.py` | Add tests for `page_react_dep()` and updated `page_react()`. |
| `docs/STATUS.md` | Remove the `HTMLDependency support for page_react()` TODO, add to recent fixes. |

## What doesn't change

- `page_bare()` — signature unchanged.
- `ui_output()` — keeps its `extra_deps` parameter (different concept: extending the base shinyjson dep within an output container).
- `render.extra_deps` class attribute — unchanged.
- `_dep()` internal function — unchanged.
