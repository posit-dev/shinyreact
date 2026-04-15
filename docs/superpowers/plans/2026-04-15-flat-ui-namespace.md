# Flat UI Namespace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `shinyjson.ui()` to `shinyjson.ui_output()`, export `page_react()` and `page_bare()` as public API, and add deferred TODOs to STATUS.md.

**Architecture:** Rename the function in `_output.py`, make the two private page functions in `_page_react.py` public (adding the shinyjson HTMLDependency to `page_react`), update `__init__.py` exports, and fix all call sites (tests, examples, `_render.py`).

**Tech Stack:** Python, htmltools, shiny

---

### Task 1: Rename `ui` to `ui_output` in `_output.py` and update tests

**Files:**
- Modify: `pkg-py/src/shinyjson/_output.py:17` (function name)
- Modify: `pkg-py/tests/test_output.py` (all references)

- [ ] **Step 1: Rename the function in `_output.py`**

In `pkg-py/src/shinyjson/_output.py`, rename `def ui(` to `def ui_output(`:

```python
def ui_output(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag:
```

No other changes to this file.

- [ ] **Step 2: Update `test_output.py` imports and calls**

In `pkg-py/tests/test_output.py`, replace the import and all calls:

```python
from shinyjson._output import ui_output
```

Rename every function call from `ui(` to `ui_output(` — there are 6 occurrences across the test functions:
- `test_ui_returns_tag`: `ui_output("my-output")`
- `test_ui_has_correct_id`: `ui_output("my-output")`
- `test_ui_has_shinyjson_class`: `ui_output("my-output")`
- `test_ui_accepts_extra_deps`: `ui_output("my-output", extra_deps=[dep])`
- `test_ui_no_extra_deps_by_default`: `ui_output("my-output")`
- `test_ui_script_has_defer`: `ui_output("my-output")`

Also rename the test functions themselves to match:
- `test_ui_returns_tag` → `test_ui_output_returns_tag`
- `test_ui_has_correct_id` → `test_ui_output_has_correct_id`
- `test_ui_has_shinyjson_class` → `test_ui_output_has_shinyjson_class`
- `test_ui_accepts_extra_deps` → `test_ui_output_accepts_extra_deps`
- `test_ui_no_extra_deps_by_default` → `test_ui_output_no_extra_deps_by_default`
- `test_ui_script_has_defer` → `test_ui_output_script_has_defer`

- [ ] **Step 3: Run tests to verify rename works**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && uv run pytest pkg-py/tests/test_output.py -v`
Expected: All 6 tests PASS with their new names.

- [ ] **Step 4: Commit**

```bash
git add pkg-py/src/shinyjson/_output.py pkg-py/tests/test_output.py
git commit -m "refactor: rename ui() to ui_output() in _output.py and tests"
```

---

### Task 2: Make page functions public and add shinyjson dep to `page_react`

**Files:**
- Modify: `pkg-py/src/shinyjson/_page_react.py` (rename functions, add dep)

- [ ] **Step 1: Write tests for `page_bare` and `page_react`**

Create `pkg-py/tests/test_page.py`:

```python
from htmltools import Tag

from shinyjson._page_react import page_bare, page_react


def test_page_bare_returns_tag():
    result = page_bare()
    assert isinstance(result, Tag)


def test_page_bare_with_title():
    result = page_bare(title="Test Page")
    rendered = str(result.tagify())
    assert "Test Page" in rendered


def test_page_bare_no_shinyjson_dep():
    result = page_bare()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyjson" not in dep_names


def test_page_react_returns_tag():
    result = page_react()
    assert isinstance(result, Tag)


def test_page_react_has_root_div():
    result = page_react()
    rendered = str(result.tagify())
    assert 'id="root"' in rendered


def test_page_react_includes_shinyjson_dep():
    result = page_react()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyjson" in dep_names


def test_page_react_includes_js_file():
    result = page_react(js_file="app.js")
    rendered = str(result.tagify())
    assert 'src="app.js"' in rendered


def test_page_react_includes_css_file():
    result = page_react(css_file="app.css")
    rendered = str(result.tagify())
    assert 'href="app.css"' in rendered


def test_page_react_default_files():
    result = page_react()
    rendered = str(result.tagify())
    assert 'src="main.js"' in rendered
    assert 'href="main.css"' in rendered
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && uv run pytest pkg-py/tests/test_page.py -v`
Expected: FAIL — `page_bare` and `page_react` cannot be imported (only `_page_bare` and `_page_react` exist).

- [ ] **Step 3: Update `_page_react.py` — rename functions and add shinyjson dep**

Replace the full contents of `pkg-py/src/shinyjson/_page_react.py` with:

```python
from __future__ import annotations

from htmltools import Tag, TagList, tags

from ._output import _dep


def page_bare(
    *args: Tag | TagList | str,
    title: str | None = None,
    lang: str = "en",
) -> Tag:
    """Create a bare HTML page with only Shiny dependencies.

    This is the escape hatch for fully custom setups that don't need the
    shinyjson JS/CSS. It wraps ``shiny.ui.page_bootstrap()`` with minimal
    defaults.

    Args:
        *args: Child tags to include in the page body.
        title: Page title.
        lang: HTML ``lang`` attribute.
    """
    from shiny.ui import page_bootstrap

    head_content = TagList()
    if title:
        head_content = TagList(tags.title(title))

    return page_bootstrap(
        head_content,
        *args,
        title=title,
        lang=lang,
    )


def page_react(
    *args: Tag | TagList | str,
    title: str | None = None,
    js_file: str = "main.js",
    css_file: str = "main.css",
    lang: str = "en",
) -> Tag:
    """Create a full-page React app served by Shiny.

    Creates an HTML page with the shinyjson dependency, a ``#root`` div for
    mounting a React app, and ``<script>``/``<link>`` tags for the provided
    JS/CSS files. Shiny runs in the background for reactivity.

    Args:
        *args: Additional child tags to include in the page body.
        title: Page title.
        js_file: Path to the main JS bundle.
        css_file: Path to the main CSS file.
        lang: HTML ``lang`` attribute.
    """
    # TODO: Accept extra_deps: list[HTMLDependency] instead of / in addition
    # to js_file/css_file string paths.
    return page_bare(
        _dep(),
        tags.link(rel="stylesheet", href=css_file),
        tags.div(id="root"),
        *args,
        tags.script(src=js_file, type="module"),
        title=title,
        lang=lang,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && uv run pytest pkg-py/tests/test_page.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyjson/_page_react.py pkg-py/tests/test_page.py
git commit -m "feat: make page_bare and page_react public, add shinyjson dep to page_react"
```

---

### Task 3: Update `__init__.py` and `_render.py` exports

**Files:**
- Modify: `pkg-py/src/shinyjson/__init__.py`
- Modify: `pkg-py/src/shinyjson/_render.py:7,79`

- [ ] **Step 1: Update `__init__.py`**

Replace the full contents of `pkg-py/src/shinyjson/__init__.py` with:

```python
from ._output import ui_output
from ._page_react import page_bare, page_react
from ._post_message import post_message
from ._render import render
from ._spec import Element, Node, Spec

__all__ = [
    "Element",
    "Node",
    "Spec",
    "page_bare",
    "page_react",
    "post_message",
    "render",
    "ui_output",
]
```

- [ ] **Step 2: Update `_render.py` import**

In `pkg-py/src/shinyjson/_render.py`, change line 7:

```python
from ._output import ui_output
```

And update `auto_output_ui` at line 79:

```python
    def auto_output_ui(self) -> Tag:
        # Express mode: auto-generate the output container.
        # extra_deps allows downstream subclasses to inject their JS/CSS.
        return ui_output(self.output_id, extra_deps=self.extra_deps)
```

- [ ] **Step 3: Run full test suite**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && uv run pytest pkg-py/tests/ -v`
Expected: All tests PASS.

- [ ] **Step 4: Run type checker**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && make py-check-types`
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyjson/__init__.py pkg-py/src/shinyjson/_render.py
git commit -m "refactor: update exports and _render.py for ui_output rename"
```

---

### Task 4: Update all examples

**Files:**
- Modify: `examples/1-hello-world/app.py:16`
- Modify: `examples/2-inputs/app.py:17`
- Modify: `examples/3-outputs/app.py:26`
- Modify: `examples/4-messages/app.py:17`
- Modify: `examples/5-shadcn/app.py:35`
- Modify: `examples/6-dashboard/app.py:20`
- Modify: `examples/7-chat/app.py:30`
- Modify: `examples/8-modules/app.py:16`
- Modify: `examples/9-blended/app.py:53`

- [ ] **Step 1: Replace `shinyjson.ui(` with `shinyjson.ui_output(` in all 9 example apps**

Each file has exactly one occurrence. The change is the same in every file:

`shinyjson.ui(` → `shinyjson.ui_output(`

For example, `examples/1-hello-world/app.py` line 16:
```python
app_ui = shinyjson.ui_output("hello", extra_deps=[_hello_dep])
```

`examples/2-inputs/app.py` line 17:
```python
app_ui = shinyjson.ui_output("main", extra_deps=[_inputs_dep])
```

`examples/3-outputs/app.py` line 26:
```python
app_ui = shinyjson.ui_output("main", extra_deps=[_outputs_dep])
```

`examples/4-messages/app.py` line 17:
```python
app_ui = shinyjson.ui_output("main", extra_deps=[_messages_dep])
```

`examples/5-shadcn/app.py` line 35:
```python
app_ui = shinyjson.ui_output("main", extra_deps=[_shadcn_dep])
```

`examples/6-dashboard/app.py` line 20:
```python
app_ui = shinyjson.ui_output("main", extra_deps=[_dashboard_dep])
```

`examples/7-chat/app.py` line 30:
```python
app_ui = shinyjson.ui_output("main", extra_deps=[_chat_dep])
```

`examples/8-modules/app.py` line 16:
```python
app_ui = shinyjson.ui_output("main", extra_deps=[_modules_dep])
```

`examples/9-blended/app.py` line 53:
```python
app_ui = shinyjson.ui_output("main", extra_deps=[_blended_dep])
```

Note: `examples/hello-shinyjson/app.py` uses Shiny Express mode (`ui.page_opts`) and does NOT call `shinyjson.ui()` directly — no change needed.

- [ ] **Step 2: Run format check**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && make py-format`
Expected: No changes (the rename doesn't affect formatting).

- [ ] **Step 3: Commit**

```bash
git add examples/*/app.py
git commit -m "refactor: update examples from shinyjson.ui() to shinyjson.ui_output()"
```

---

### Task 5: Update STATUS.md with TODOs and recent fix

**Files:**
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Update the "Full React page support" TODO**

Replace the existing "Full React page support" TODO in `docs/STATUS.md` with an updated version that reflects the new public API and remaining work:

```markdown
### Full React page support

`page_react()` and `page_bare()` are now exported. `page_react()` creates a full-page React app with a `#root` div and the shinyjson HTMLDependency. Remaining work:
- End-to-end example app demonstrating the full React SPA pattern.
- Ensure all hooks and the output binding gracefully handle late Shiny arrival.
```

- [ ] **Step 2: Add deferred TODOs**

Add these three new TODOs to the `## TODOs` section in `docs/STATUS.md`:

```markdown
### Nest UI functions into `shinyjson.ui.*` submodule

Currently `ui_output`, `page_react`, and `page_bare` are flat top-level exports. Later, restructure into a `shinyjson.ui` submodule: `ui.output()`, `ui.page_react()`, `ui.page_bare()`.

### `HTMLDependency` support for `page_react()`

`page_react()` currently accepts `js_file`/`css_file` string paths. Consider accepting `extra_deps: list[HTMLDependency]` instead of or in addition to string paths, for consistency with the rest of the API.

### Evaluate `extra_deps` on `ui_output()`

Should HTML dependencies be handled exclusively at the render subclass or page level? If so, `extra_deps` could be removed from `ui_output()` to simplify the API.
```

- [ ] **Step 3: Add to recent fixes**

Add this bullet under `## Recent fixes`:

```markdown
- **Flat UI namespace**: Renamed `shinyjson.ui()` to `shinyjson.ui_output()`. Exported `page_react()` and `page_bare()` as public API. `page_react()` includes the shinyjson HTMLDependency automatically.
```

- [ ] **Step 4: Commit**

```bash
git add docs/STATUS.md
git commit -m "docs: update STATUS.md for flat UI namespace changes"
```

---

### Task 6: Final validation

- [ ] **Step 1: Run full Python checks**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && make py-check`
Expected: All format checks, type checks, and tests pass.

- [ ] **Step 2: Verify no remaining references to old `shinyjson.ui(`**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && grep -r 'shinyjson\.ui(' --include='*.py' .`
Expected: No matches (the grep should return empty).

- [ ] **Step 3: Verify exports work**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/kolkata && uv run python -c "import shinyjson; print(shinyjson.ui_output); print(shinyjson.page_react); print(shinyjson.page_bare)"`
Expected: Prints three function references without error.
