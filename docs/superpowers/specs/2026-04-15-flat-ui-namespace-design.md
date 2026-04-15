# Flat UI namespace: `ui_output`, `page_react`, `page_bare`

## Summary

Restructure shinyjson's Python public API to export page-level functions and rename `ui()` to `ui_output()`. All three functions live at the top level of the `shinyjson` namespace.

## Motivation

shinyjson currently exports `ui(id, extra_deps)` which creates a single output placeholder div. There is no public API for creating a full page layout. A private `_page_react()` function exists but is not exported. Apps that want a full React SPA page or a bare page have no shinyjson-provided solution.

Additionally, `shinyjson.ui` as a function name occupies a name that would naturally be a submodule (like `shiny.ui`). Renaming to `ui_output` frees the `ui` name for future nesting.

## API

```python
import shinyjson

# Output placeholder — creates a <div class="shinyjson-output"> with the shinyjson HTMLDependency.
# Renamed from shinyjson.ui().
shinyjson.ui_output(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag

# Full React SPA page — page_bootstrap with shinyjson HTMLDependency, a #root div,
# and script/stylesheet tags for the provided js/css files.
shinyjson.page_react(
    *args: Tag | TagList | str,
    title: str | None = None,
    js_file: str = "main.js",
    css_file: str = "main.css",
    lang: str = "en",
) -> Tag

# Bare page — page_bootstrap with no shinyjson dep. Escape hatch for fully custom setups.
shinyjson.page_bare(
    *args: Tag | TagList | str,
    title: str | None = None,
    lang: str = "en",
) -> Tag
```

## Implementation

### File changes

1. **`_output.py`**: Rename `ui()` to `ui_output()`.
2. **`_page_react.py`**: Make `_page_react()` and `_page_bare()` public (remove leading underscores). `page_react()` adds the shinyjson HTMLDependency (from `_output.py._dep()`).
3. **`__init__.py`**: Update exports:
   - `from ._output import ui_output`
   - `from ._page_react import page_bare, page_react`
   - Add all three to `__all__`.
4. **All examples**: Replace `shinyjson.ui(...)` with `shinyjson.ui_output(...)`.
5. **Tests**: Update any references to `shinyjson.ui()`.

### `page_react()` behavior

- Calls `page_bare()` internally.
- Adds the shinyjson HTMLDependency (`_dep()` from `_output.py`).
- Adds a `<link rel="stylesheet" href=css_file>` tag.
- Adds a `<div id="root">` element.
- Adds a `<script src=js_file type="module">` tag.
- Passes through `*args`, `title`, and `lang` to `page_bare()`.

### `page_bare()` behavior

- Wraps `shiny.ui.page_bootstrap()`.
- Adds a `<title>` tag if `title` is provided.
- No shinyjson dependency included.

## Breaking changes

- `shinyjson.ui(id)` is removed. Use `shinyjson.ui_output(id)` instead.
- This is acceptable because shinyjson is not yet widely published; only in-repo examples are affected.

## Deferred TODOs

1. **Nest into `shinyjson.ui.*` submodule**: Later, restructure so `ui_output` becomes `ui.output`, `page_react` becomes `ui.page_react`, etc.
2. **`HTMLDependency` support for `page_react()`**: Accept `extra_deps: list[HTMLDependency]` instead of / in addition to `js_file`/`css_file` string paths.
3. **Evaluate `extra_deps` on `ui_output()`**: Should deps be handled exclusively at the render subclass or page level, removing `extra_deps` from `ui_output()`?
