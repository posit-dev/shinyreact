# Shared mtime helper for cache-busting + stat-cached `index.html`

**Date:** 2026-05-12
**Status:** Proposal — pending decision
**Related:** #82 (set_react_page caches index.html), #84 (_dep version pinned)

## Summary

Introduce a single shared primitive — `_file_mtime_int(path) -> int | None` — and use it at every site in the package that currently reads file mtimes. Use it inside `_build_react_page_fn` to stat-cache `index.html` so the file is re-read only when its mtime changes, not on every render.

## Context

The fixes for #82 and #84 each introduced their own mtime handling:

- **`_dep()`** (`pkg-py/src/shinyreact/_output.py`) — `str(int(_SHINYREACT_JS_PATH.stat().st_mtime)) if _SHINYREACT_JS_PATH.exists() else "0.1.0"`. Stamps `HTMLDependency.version` so the browser re-fetches the JS bundle after a rebuild.
- **`_build_react_page_fn`** (`pkg-py/src/shinyreact/_page.py`) — currently re-reads `index.html` on every page render. Cheap, but unnecessary I/O.
- **`page_react_dep`** (`pkg-py/src/shinyreact/_page.py`) — `str(int(js_path.stat().st_mtime)) if js_path.exists() else "0"`. Same dance, different fallback.

Three near-identical patterns. A small shared helper removes the duplication and lets `_build_react_page_fn` cheaply detect "did the file change?" instead of unconditionally re-reading.

## Design

### Helper

In `pkg-py/src/shinyreact/_output.py`:

```python
def _file_mtime_int(path: Path) -> int | None:
    """Return the file's mtime in whole seconds, or None if it doesn't exist."""
    try:
        return int(path.stat().st_mtime)
    except FileNotFoundError:
        return None
```

### Call sites

**`_dep()`** — same module:

```python
mtime = _file_mtime_int(_SHINYREACT_JS_PATH)
version = str(mtime) if mtime is not None else "0.1.0"
```

**`page_react_dep()`** — imports from `_output`:

```python
mtime = _file_mtime_int(js_path)
version = str(mtime) if mtime is not None else "0"
```

**`_build_react_page_fn()`** — closure-scoped stat cache:

```python
def _build_react_page_fn(index_path: Path) -> Callable[..., Tag]:
    if not index_path.exists():
        raise FileNotFoundError(f"HTML file not found: {index_path}")

    cached_mtime: int | None = None
    cached_html: str = ""

    def _react_page_fn(*args: Any) -> Tag:
        nonlocal cached_mtime, cached_html

        mtime = _file_mtime_int(index_path)
        if mtime != cached_mtime:
            cached_mtime = mtime
            cached_html = index_path.read_text() if mtime is not None else ""

        deps: list[HTMLDependency] = []
        for arg in args:
            if isinstance(arg, Renderer):
                ui = arg.auto_output_ui()
                if isinstance(ui, (Tag, TagList)):
                    deps.extend(ui.get_dependencies())

        return cast(Tag, TagList(_dep(), *deps, HTML(cached_html)))

    return _react_page_fn
```

If `index.html` is deleted between renders, `mtime` becomes `None` and we serve an empty string. A subsequent restore re-populates the cache. The construction-time `exists()` check still guards against typo'd paths at app startup.

## Testing

- Update `test_build_page_fn_rereads_index_html_per_render` (introduced in the #82 fix) to remain accurate — the test asserts post-edit content is served on the next render, which still holds.
- Add `test_build_page_fn_does_not_reread_when_mtime_unchanged` — patch `Path.read_text` (or wrap a counter around it) and assert it's called once across multiple renders when the file hasn't changed.
- Existing `test_dep_version_tracks_bundle_mtime` and `test_page_react_dep_uses_mtime_version` keep working unchanged — they assert observable behaviour, not implementation.

## Non-goals

- Content-hash versioning (issue #84 option 2). Would be more accurate across redeploys but is out of scope for this refactor.
- A general-purpose stat-cache class. Single small primitive is enough.
- Caching the `HTMLDependency` object itself in `_dep()`. Each call constructs a fresh one — left alone.
