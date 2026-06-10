# Remove vestigial `#root` from `page_react()`

**Issue:** [#143](https://github.com/posit-dev/shinyreact/issues/143) — Make sure DOM element `#root` isn't required for the app.py pattern.

## Problem

`page_react()` emits a `<div id="root">` in both Python (`pkg-py/src/shinyreact/_page.py`) and R (`pkg-r/R/page.R`). This is leftover from early SPA demos. The shinyreact JS bundle never mounts into `#root` — it only renders into `.shinyreact-output` elements (the Shiny output binding) and `.shinyreact-static` mounts (inline-spec seeding). There is no `getElementById("root")` anywhere in the active JS.

So for the **app.py pattern** (`output_react()` placeholders + `render_react`), the `#root` div is dead markup. The goal is to remove it so `page_react()` emits clean page chrome, and to prove via tests that the app.py pattern renders without `#root`.

### Current consumers of the emitted `#root`

Two examples self-mount a React app into the `#root` div that `page_react()` emits:

- `examples/app-py/11-hello-spa-old/main.js` — `createRoot(getElementById("root"))`
- `examples/app-py/13-bookmarking/bookmarking.js` — `createRoot(getElementById("root"))`

Removing `#root` from `page_react()` breaks these two; they are migrated (below). All ui.tsx examples and Playwright test apps serve their own `www/index.html` with its own `#root` and do **not** go through `page_react()` — they are unaffected.

### API asymmetry uncovered

`set_react_page()` is **Express-only** (it calls `page_opts`). Python has no Core-mode way to serve a static `www/index.html`; only R has that via `page_react_html()`. The `app-core.py` example (below) needs the Core-mode path, so this design adds a Python `page_react_html()` mirroring R's.

## Changes

### 1. Core library — drop `#root`

- `page_react()` no longer emits `<div id="root">`, in Python (`pkg-py/src/shinyreact/_page.py`) and R (`pkg-r/R/page.R`). It becomes pure page chrome: the shinyreact page-level dependency (bundle + bookmark-restore script) plus the caller's children.
- Update the docstrings in both files to remove the "`#root` div" language.

The app.py pattern (`output_react()` placeholders) is unaffected. Self-mounting apps now supply their own mount point or mount into `document.body`.

### 2. New Python public API — `page_react_html(path="www/index.html")`

- Mirrors R's existing `page_react_html()`: reads an HTML file, attaches the shinyreact page-level dependency, and returns a UI object usable as `App(ui=..., server=...)` — the **Core-mode** counterpart to the Express-only `set_react_page()`.
- Lives in `pkg-py/src/shinyreact/_page.py` and is exported from `shinyreact/__init__.py`.
- It is the simple static server (like R's): it does **not** do the renderer dependency auto-discovery that `set_react_page()` performs. That remains a `set_react_page()` feature.
- Path resolution should follow the same convention as `set_react_page()` (absolute used verbatim; relative resolves against the caller module's directory, falling back to `Path.cwd()` when there is no caller `__file__`). Raises `FileNotFoundError` when the file is missing.

### 3. Examples

**Delete `examples/app-py/11-hello-spa-old/`** and replace its role with a Core-API entry in the existing ui.tsx hello example.

**Add `examples/ui-tsx/01-hello/app-core.py`** — the Core-API twin of the existing Express `app.py`, serving the *same* `www/index.html` + `www/app.js` via the new `page_react_html()`:

```python
from shiny import App, Inputs, Outputs, Session, reactive
from shinyreact import page_react_html, reactive_output

app_ui = page_react_html()  # serves www/index.html (Core)


def server(input: Inputs, output: Outputs, session: Session):
    @reactive.calc
    def greeting():
        name = input.name()
        return name if name else "World"

    @reactive_output
    def txtout_title():
        return f"Hello, {greeting()}!"

    @reactive_output
    def txtout_count():
        return input.click_count()


app = App(app_ui, server)
```

`11-hello-spa-old`'s own server logic (single uppercase `txtout`) and its `main.js`/`styles.css` are not carried over — its role as the legacy inline-SPA demo is superseded by `01-hello` showing both Express (`app.py`) and Core (`app-core.py`) entries against one shared client.

Update `examples/ui-tsx/01-hello/README.md` to document `app-core.py` (Core) alongside `app.py` (Express), including the Layout and Run sections.

**`examples/app-py/13-bookmarking/bookmarking.js`** — mount into `document.body` instead of `#root`:

```js
window.shinyreact.ReactDOM.createRoot(document.body).render(h(App));
```

This demonstrates that no container div is required. (React mounting into `document.body` is generally discouraged because other scripts may mutate body, but with the shinyreact bundle it is fine for this example and makes the point directly.) The `13-bookmarking/README.md` does not currently mention a root div, so no change is expected there; verify during implementation.

### 4. Tests

- `pkg-py/tests/test_page.py` — invert the assertion at the `page_react` test: assert the rendered output does **not** contain `id="root"`. Add a test that `page_react(output_react("x"))` still renders the `.shinyreact-output` placeholder (the app.py pattern works without `#root`).
- New `page_react_html()` tests (Python), mirroring R's `test-page.R`: serves the file's HTML, attaches the page dependency, raises on a missing file.
- `pkg-r/tests/testthat/test-page.R` — invert the `page_react includes #root` assertion to `expect_no_match(html, 'id="root"')`. R's existing `page_react_html` tests stay.

These cover the "verify `#root` isn't required" the issue asks for; each should fail before the change and pass after.

### 5. Docs

- `docs/features.md` — drop "`#root`" from the `page_react()` descriptions (lines ~16 and ~113–114); add a `page_react_html()` (Python) row.
- `CLAUDE.md` architecture section — add `page_react_html()` as the Python Core counterpart to the Express-only `set_react_page()`, parallel to the existing R note.
- `docs/todos.md` — update the `page_react()` description that mentions `#root`.

## Out of scope

- ui.tsx `www/index.html` files keep their own `#root` — that is the user-authored mount for the ui.tsx pattern, untouched by this issue.
- No change to `output_react()`, the JS bundle, or `set_react_page()` behavior.

## Verification

- `make py-check` (format + types + tests) passes.
- `make r-check` passes (including the inverted `test-page.R`).
- The `13-bookmarking` example loads and bookmarks/restores correctly with the body-mounted client.
- `examples/ui-tsx/01-hello/app-core.py` runs and shows the same two cards as the Express `app.py`.
