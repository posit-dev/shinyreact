# Remove vestigial `#root` from `page_react()` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop `page_react()` from emitting a vestigial `<div id="root">`, add a Python Core-mode `page_react_html()`, and migrate the two examples that self-mounted into `#root`.

**Architecture:** `page_react()` (Python + R) becomes pure page chrome (shinyreact dep + bookmark-restore script + children). The app.py pattern (`output_react()` placeholders) was never affected by `#root`; we add tests proving it. Self-mounting apps now mount into `document.body` (the `13-bookmarking` example) or use the new Core-mode `page_react_html()` to serve a static `www/index.html` (the relocated hello example).

**Tech Stack:** Python (hatchling, pytest, htmltools/shiny), R (testthat, htmltools), no-build JS examples.

**Reference spec:** `docs/superpowers/specs/2026-06-10-page-react-no-root-design.md`

---

### Task 1: R — drop `#root` from `page_react()`

**Files:**
- Modify: `pkg-r/R/page.R:14-31`
- Test: `pkg-r/tests/testthat/test-page.R:1-7`

- [ ] **Step 1: Update the test to assert no `#root`**

Replace the first test block (`pkg-r/tests/testthat/test-page.R:1-7`) with:

```r
test_that("page_react emits no #root div but includes the shinyreact dep", {
  ui <- page_react()
  html <- as.character(ui)
  expect_no_match(html, 'id="root"')
  deps <- htmltools::findDependencies(ui)
  expect_true(any(vapply(deps, function(d) d$name == "shinyreact", logical(1))))
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd pkg-r && Rscript -e 'testthat::test_file("tests/testthat/test-page.R")'`
Expected: FAIL — the `expect_no_match` fails because `page_react()` still emits `id="root"`.

- [ ] **Step 3: Remove the `#root` div and update the docstring**

In `pkg-r/R/page.R`, change the roxygen line 16 from:

```r
#' Creates a page with a `#root` div and the shinyreact page-level dependency
```

to:

```r
#' Creates a page with the shinyreact page-level dependency
```

Then delete the `htmltools::tags$div(id = "root"),` line so the function body reads:

```r
page_react <- function(..., title = NULL, lang = "en") {
  page_bare(
    shinyreact_dep_page(),
    ...,
    title = title,
    lang = lang
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd pkg-r && Rscript -e 'testthat::test_file("tests/testthat/test-page.R")'`
Expected: PASS (all four tests in the file).

- [ ] **Step 5: Format and commit**

```bash
make r-format
git add pkg-r/R/page.R pkg-r/tests/testthat/test-page.R
git commit -m "fix(r): page_react() no longer emits a #root div (#143)"
```

---

### Task 2: Python — drop `#root` from `page_react()`

**Files:**
- Modify: `pkg-py/src/shinyreact/_page.py:47-72`
- Test: `pkg-py/tests/test_page.py:28-31`

- [ ] **Step 1: Replace the `#root` assertion test and add an app.py-pattern render test**

In `pkg-py/tests/test_page.py`, replace `test_page_react_has_root_div` (lines 28-31) with:

```python
def test_page_react_emits_no_root_div():
    result = page_react()
    rendered = str(result.tagify())
    assert 'id="root"' not in rendered


def test_page_react_renders_output_placeholder():
    """The app.py pattern works without a #root div."""
    from shinyreact import output_react

    result = page_react(output_react("hello"))
    rendered = str(result.tagify())
    assert "shinyreact-output" in rendered
    assert 'id="hello"' in rendered
```

- [ ] **Step 2: Run the tests to verify the first one fails**

Run: `uv run pytest pkg-py/tests/test_page.py::test_page_react_emits_no_root_div -v`
Expected: FAIL — `page_react()` still emits `id="root"`.

- [ ] **Step 3: Remove the `#root` div and update the docstring**

In `pkg-py/src/shinyreact/_page.py`, change the docstring lines 54-55 from:

```python
    Creates an HTML page with the shinyreact dependency and a ``#root`` div for
    mounting a React app. Shiny runs in the background for reactivity.
```

to:

```python
    Creates an HTML page with the shinyreact dependency. Shiny runs in the
    background for reactivity.
```

Then delete the `tags.div(id="root"),` line so the return reads:

```python
    return page_bare(
        _dep_page(),
        *args,
        title=title,
        lang=lang,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest pkg-py/tests/test_page.py -v`
Expected: PASS (all tests in the file).

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyreact/_page.py pkg-py/tests/test_page.py
git commit -m "fix(py): page_react() no longer emits a #root div (#143)"
```

---

### Task 3: Python — add Core-mode `page_react_html()`

**Files:**
- Modify: `pkg-py/src/shinyreact/_page.py` (add function after `set_react_page` / `_build_react_page_fn`)
- Modify: `pkg-py/src/shinyreact/__init__.py:1-22`
- Test: `pkg-py/tests/test_page.py`

- [ ] **Step 1: Write failing tests for `page_react_html()`**

Append to `pkg-py/tests/test_page.py`:

```python
def test_page_react_html_attaches_dep(tmp_path):
    from shinyreact import page_react_html

    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    ui = page_react_html(index)
    deps = ui.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyreact" in dep_names


def test_page_react_html_includes_file_html(tmp_path):
    from shinyreact import page_react_html

    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    ui = page_react_html(index)
    rendered = str(ui.tagify())
    assert 'id="root"' in rendered  # the user's own mount, from their file


def test_page_react_html_missing_file_raises(tmp_path):
    from shinyreact import page_react_html

    with pytest.raises(FileNotFoundError, match="not found"):
        page_react_html(tmp_path / "nope.html")
```

Add `import pytest` at the top of the file if not already present (it is not — add it on a new line after the existing imports at the top).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest pkg-py/tests/test_page.py -k page_react_html -v`
Expected: FAIL — `cannot import name 'page_react_html'`.

- [ ] **Step 3: Implement `page_react_html()`**

In `pkg-py/src/shinyreact/_page.py`, add this function (place it after `set_react_page` and its `_build_react_page_fn` helper). It reuses the same path-resolution convention as `set_react_page` but returns a UI object usable as `App(ui=..., server=...)` instead of calling `page_opts`:

```python
def page_react_html(path: str | Path = "www/index.html") -> TagList:
    """Serve a static React ``index.html`` (the ui.tsx pattern, Core API).

    The Core-mode counterpart to :func:`set_react_page`. Reads an HTML file,
    attaches the shinyreact page-level dependency, and returns UI suitable for
    use as the ``ui`` argument of :class:`shiny.App`. Use this when you write a
    Core-style app (``App(app_ui, server)``); use :func:`set_react_page` for
    Shiny Express apps.

    Unlike :func:`set_react_page`, this does not auto-discover dependencies
    from traditional Shiny renderers — it only attaches the shinyreact bundle.

    Args:
        path: Path to the HTML file. Absolute paths are used verbatim;
            relative paths resolve against the caller module's directory, or
            against :func:`pathlib.Path.cwd` when there is no caller
            ``__file__``. Defaults to ``"www/index.html"``.
    """
    path = Path(path)
    if path.is_absolute():
        index_path = path
    else:
        caller_file = sys._getframe(1).f_globals.get("__file__")
        caller_dir = Path(caller_file).parent if caller_file else Path.cwd()
        index_path = caller_dir / path
    if not index_path.exists():
        raise FileNotFoundError(f"HTML file not found: {index_path}")
    index_html = index_path.read_text()
    return TagList(_dep_page(), HTML(index_html))
```

- [ ] **Step 4: Export it from the package**

In `pkg-py/src/shinyreact/__init__.py`, update the `_page` import and `__all__`:

```python
from ._page import (
    page_bare,
    page_react,
    page_react_dep,
    page_react_html,
    set_react_page,
)
```

and add `"page_react_html",` to `__all__` (keep it alphabetically near the other `page_*` entries):

```python
    "page_bare",
    "page_react",
    "page_react_dep",
    "page_react_html",
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest pkg-py/tests/test_page.py -v`
Expected: PASS (all tests).

- [ ] **Step 6: Type-check and commit**

```bash
make py-check-types
git add pkg-py/src/shinyreact/_page.py pkg-py/src/shinyreact/__init__.py pkg-py/tests/test_page.py
git commit -m "feat(py): add page_react_html() Core-mode ui.tsx page helper (#143)"
```

---

### Task 4: Example — `13-bookmarking` mounts into `document.body`

**Files:**
- Modify: `examples/app-py/13-bookmarking/bookmarking.js:82-83`

- [ ] **Step 1: Change the mount target**

In `examples/app-py/13-bookmarking/bookmarking.js`, replace lines 82-83:

```js
  var root = window.shinyreact.ReactDOM.createRoot(document.getElementById("root"));
  root.render(h(App));
```

with:

```js
  var root = window.shinyreact.ReactDOM.createRoot(document.body);
  root.render(h(App));
```

- [ ] **Step 2: Verify the README needs no change**

Run: `grep -n "root" examples/app-py/13-bookmarking/README.md`
Expected: no match for a `#root` / "root div" reference. If a match appears that describes a root div, remove that sentence; otherwise leave the README unchanged.

- [ ] **Step 3: Smoke-test the example loads**

Run: `uv run shiny run examples/app-py/13-bookmarking/app.py --port 0` (Ctrl-C after it prints the URL and you confirm no startup error). Optional manual check: the page renders the form and bookmarking still round-trips via the URL.

- [ ] **Step 4: Commit**

```bash
git add examples/app-py/13-bookmarking/bookmarking.js
git commit -m "example(13-bookmarking): mount React into document.body, not #root (#143)"
```

---

### Task 5: Example — relocate the legacy SPA demo to `ui-tsx/01-hello/app-core.py`

**Files:**
- Create: `examples/ui-tsx/01-hello/app-core.py`
- Delete: `examples/app-py/11-hello-spa-old/` (entire directory)
- Modify: `examples/ui-tsx/01-hello/README.md`

- [ ] **Step 1: Create the Core-API entry**

Create `examples/ui-tsx/01-hello/app-core.py` — the Core twin of the existing Express `app.py`, serving the same `www/index.html` + `www/app.js`:

```python
from shiny import App, Inputs, Outputs, Session, reactive
from shinyreact import page_react_html, reactive_output

app_ui = page_react_html()  # serves www/index.html (Core API)


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

- [ ] **Step 2: Verify it runs**

Run: `uv run shiny run examples/ui-tsx/01-hello/app-core.py --port 0` (Ctrl-C after the URL prints with no startup error). The page should render the same two cards (Client + Server) as the Express `app.py`.

- [ ] **Step 3: Delete the legacy example**

```bash
git rm -r examples/app-py/11-hello-spa-old
```

- [ ] **Step 4: Update the README**

In `examples/ui-tsx/01-hello/README.md`, update the **Layout** block to add `app-core.py`, and the **Run it** section to mention both entries. Change the Layout block to:

```
examples/ui-tsx/01-hello/
├── app.py            # Express: set_react_page() + 2 reactive_output outputs
├── app-core.py       # Core: page_react_html() + App(app_ui, server), same outputs
└── www/
    ├── index.html    # 3 lines: stylesheet, #root div, script
    ├── app.js        # raw React.createElement (with `h` shorthand)
    └── main.css      # body reset
```

And change the **Run it** section from the single command to:

```bash
# Express API
uv run shiny run examples/ui-tsx/01-hello/app.py

# Core API (same client, same outputs)
uv run shiny run examples/ui-tsx/01-hello/app-core.py
```

Add one sentence under the existing intro noting that `app.py` (Express, via `set_react_page()`) and `app-core.py` (Core, via `page_react_html()`) are two server-side entries for the same `www/` client.

- [ ] **Step 5: Commit**

```bash
git add examples/ui-tsx/01-hello/app-core.py examples/ui-tsx/01-hello/README.md
git commit -m "example(ui-tsx/01-hello): add Core-API app-core.py; remove legacy 11-hello-spa-old (#143)"
```

---

### Task 6: Docs — update `#root` references and document `page_react_html()` (Python)

**Files:**
- Modify: `docs/features.md:16`, `docs/features.md:113`
- Modify: `docs/todos.md:47`
- Modify: `CLAUDE.md:108`, `CLAUDE.md:116`

- [ ] **Step 1: Update `docs/features.md`**

Change line 16 from:

```
| `shinyreact.page_react()` | Working | Full-page React app with `#root` + the shinyreact HTMLDependency |
```

to (two rows — update `page_react`, add `page_react_html`):

```
| `shinyreact.page_react()` | Working | Full-page React app chrome + the shinyreact HTMLDependency (app.py pattern) |
| `shinyreact.page_react_html()` | Working | Core-mode helper serving a static `www/index.html` (ui.tsx pattern); Core counterpart to `set_react_page()` |
```

Change line 113 from:

```
| `page_react(...)` | Working | Full-page React app with `#root` + page-level dep (bundle + bookmark restore script) |
```

to:

```
| `page_react(...)` | Working | Full-page React app chrome + page-level dep (bundle + bookmark restore script) |
```

- [ ] **Step 2: Update `docs/todos.md`**

Change line 47 from:

```
`page_react()` and `page_bare()` are now exported. `page_react()` creates a full-page React app with a `#root` div and the shinyreact HTMLDependency. Remaining work:
```

to:

```
`page_react()` and `page_bare()` are now exported. `page_react()` creates full-page React app chrome with the shinyreact HTMLDependency. Remaining work:
```

- [ ] **Step 3: Update `CLAUDE.md`**

Change line 108 (add a sentence introducing the Core counterpart). After the existing `set_react_page` bullet, add a new bullet:

```
- `shinyreact.page_react_html(path="www/index.html")` — Core-mode helper that serves a static `www/index.html` (the ui.tsx pattern) as the `ui` argument of `App(ui=..., server=...)`; attaches the shinyreact dep. The Core counterpart to the Express-only `set_react_page()`.
```

Change line 116 from:

```
- `page_react_html(path = "www/index.html")` is R's equivalent of Python's `set_react_page()` (the ui.tsx pattern entry).
```

to:

```
- `page_react_html(path = "www/index.html")` matches Python's `page_react_html()` (Core-mode ui.tsx entry); Python additionally has the Express-only `set_react_page()`.
```

- [ ] **Step 4: Commit**

```bash
git add docs/features.md docs/todos.md CLAUDE.md
git commit -m "docs: page_react() emits no #root; document Python page_react_html() (#143)"
```

---

### Task 7: Full verification

- [ ] **Step 1: Python checks**

Run: `make py-check`
Expected: format check + pyright + pytest all pass.

- [ ] **Step 2: R checks**

Run: `make r-check`
Expected: format + testthat + R CMD check pass.

- [ ] **Step 3: Confirm no stray `#root`-from-`page_react` references remain**

Run: `grep -rn "id=\"root\"" pkg-py/src pkg-r/R`
Expected: no matches (the only `#root` divs left are in user-authored `www/index.html` files and test apps, not in `page_react()`).

- [ ] **Step 4: Final commit if any formatting changed**

```bash
git add -A
git commit -m "chore: formatting after #143 changes" || echo "nothing to commit"
```
