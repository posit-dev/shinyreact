# `render_react` / `reactive_output` Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the overloaded server-side renderer into two intent-named functions in both Python and R — `render_react` (app pattern, walks UI → JSON spec, carries an `output_react` placeholder) and `reactive_output` (ui.tsx pattern, publishes a JSON value, no placeholder) — and rename the UI helper to `output_react` in both languages.

**Architecture:** Both renderers share the same runtime transform (walk `node()`/tag/`TagChild` content → JSON spec; pass `Jsonifiable` data through unchanged). The split is expressed only through (1) Python static types (`render_react: Renderer[Node | TagChild]` vs `reactive_output: Renderer[Jsonifiable]`) and (2) the default UI (`render_react.auto_output_ui()` → `output_react(id)`; `reactive_output` inherits the base `auto_output_ui()` which returns `None`). R has no runtime assertions; `reactive_output` calls `createRenderFunction` with no `outputFunc`. No backward-compatible aliases — hard rename, every call site updated.

**Tech Stack:** Python (shiny `Renderer`, htmltools, pytest), R (shiny `createRenderFunction`, roxygen2, testthat), Vite/TS examples unaffected.

**Reference spec:** `docs/superpowers/specs/2026-06-02-render-react-reactive-output-split-design.md`

**Migration rule (applies to every example/doc edit):** an output paired with an `output_react` placeholder (the **app** pattern) uses `render_react`; an output with no placeholder whose value a hook reads (the **ui.tsx** pattern) uses `reactive_output`. In practice: `examples/app-py/*` and `examples/app-r/*` use `render_react`; `examples/ui-tsx/*` and `examples/ui-tsx-r/*` use `reactive_output`.

---

## Task 1: Python — rename `ui_output` → `output_react`

**Files:**
- Modify: `pkg-py/src/shinyreact/_output.py`
- Test: `pkg-py/tests/test_output.py`

- [ ] **Step 1: Update the test file to use `output_react`**

In `pkg-py/tests/test_output.py`, change the import and every call/identifier. Replace:

```python
from shinyreact._output import _SHINYREACT_JS_PATH, _dep, ui_output
```

with:

```python
from shinyreact._output import _SHINYREACT_JS_PATH, _dep, output_react
```

Then rename each test function `test_ui_output_*` → `test_output_react_*` and replace every `ui_output(` call with `output_react(`. The five affected tests are `test_ui_output_returns_tag`, `test_ui_output_has_correct_id`, `test_ui_output_has_shinyreact_class`, `test_ui_output_accepts_extra_deps`, `test_ui_output_no_extra_deps_by_default`, `test_ui_output_script_has_defer`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest pkg-py/tests/test_output.py -q`
Expected: FAIL with `ImportError: cannot import name 'output_react'`.

- [ ] **Step 3: Rename the function in source**

In `pkg-py/src/shinyreact/_output.py`, rename `ui_output` and update its docstring to reference the new names:

```python
def output_react(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag:
    """Create a Shiny output placeholder for a shinyreact ``render_react`` renderer.

    Args:
        id: The output ID. Must match the server-side ``@shinyreact.render_react``
            function name.
        extra_deps: Additional HTML dependencies to include. Used by downstream
            packages to inject their own JS/CSS (e.g. ``shinyshadcn``).

    Returns:
        A ``<div>`` tag that the shinyreact Shiny output binding renders into.
    """
    return div(
        _dep(),
        *(extra_deps or []),
        id=id,
        class_="shinyreact-output",
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest pkg-py/tests/test_output.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyreact/_output.py pkg-py/tests/test_output.py
git commit -m "refactor(py): rename ui_output -> output_react"
```

---

## Task 2: Python — extract shared transform into `_render.py`

**Files:**
- Create: `pkg-py/src/shinyreact/_render.py`

This isolates the walk-or-passthrough logic so both renderers share one implementation.

- [ ] **Step 1: Create the shared transform module**

Create `pkg-py/src/shinyreact/_render.py`:

```python
from __future__ import annotations

from warnings import warn

from htmltools import Tag, TagList
from shiny.types import Jsonifiable

from ._spec import Node, serialize_ui


def _should_walk(value: object) -> bool:
    """True when ``value`` is htmltools/Node content to walk into the JSON wire tree.

    Bare ``str`` / ``bytes`` are excluded so JSON-string outputs in the
    ``ui.tsx`` pattern pass through unchanged.
    """
    if isinstance(value, (str, bytes)):
        return False
    if isinstance(value, (Node, Tag, TagList)):
        return True
    return hasattr(value, "tagify")


def walk_or_passthrough(value: object, output_id: str) -> Jsonifiable:
    """Walk htmltools/``Node`` content into the JSON wire tree, else pass through.

    Shared by ``render_react`` and ``reactive_output``. Emits a warning when a
    walked tree carries ``HTMLDependency`` objects that cannot reach ``<head>``
    after the page has rendered.
    """
    if _should_walk(value):
        payload, deps = serialize_ui(value)
        if deps:
            names = ", ".join(d.name for d in deps)
            warn(
                f"shinyreact: '{output_id}' returned content carrying "
                f"HTMLDependency objects ({names}) that cannot be injected "
                "after the page has rendered. Declare them up-front via "
                "output_react(..., extra_deps=[...]) or at the page level.",
                UserWarning,
                # stacklevel=2: Shiny calls transform() internally, so this
                # can't reach user code anyway.
                stacklevel=2,
            )
        return payload
    return value  # type: ignore[return-value]
```

- [ ] **Step 2: Verify it imports cleanly**

Run: `uv run python -c "from shinyreact._render import walk_or_passthrough, _should_walk; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/src/shinyreact/_render.py
git commit -m "refactor(py): extract shared walk_or_passthrough transform"
```

---

## Task 3: Python — add `render_react`, narrow `reactive_output`

**Files:**
- Create: `pkg-py/src/shinyreact/_render_react.py`
- Modify: `pkg-py/src/shinyreact/_reactive_output.py`
- Modify: `pkg-py/src/shinyreact/__init__.py`
- Create: `pkg-py/tests/test_render_react.py`
- Modify: `pkg-py/tests/test_reactive_output.py`

- [ ] **Step 1: Write the failing test for `render_react`**

Create `pkg-py/tests/test_render_react.py`:

```python
"""Tests for the render_react renderer (app.py pattern: walks UI -> JSON spec)."""

from __future__ import annotations

import pytest
from htmltools import HTMLDependency, TagList, tags
from shinyreact import Node, render_react


@pytest.mark.asyncio
async def test_node_is_walked_to_wire_tree() -> None:
    node = Node(type="Card", props={"title": "Hi"})

    @render_react
    def out():
        return node

    assert await out.transform(node) == {
        "type": "react",
        "name": "Card",
        "props": {"title": "Hi"},
        "children": [],
    }


@pytest.mark.asyncio
async def test_child_string_becomes_text_node() -> None:
    node = Node(type="Card", props={}, children=["hi"])

    @render_react
    def out():
        return node

    transformed = await out.transform(node)
    assert transformed["children"] == [{"type": "text", "value": "hi"}]


@pytest.mark.asyncio
async def test_tag_is_walked() -> None:
    @render_react
    def out():
        return tags.div("x", class_="c")

    assert await out.transform(tags.div("x", class_="c")) == {
        "type": "tag",
        "name": "div",
        "props": {"className": "c"},
        "children": [{"type": "text", "value": "x"}],
    }


@pytest.mark.asyncio
async def test_taglist_single_child_unwraps_through_transform() -> None:
    tl = TagList(tags.div("x"))

    @render_react
    def out():
        return tl

    assert await out.transform(tl) == {
        "type": "tag",
        "name": "div",
        "props": {},
        "children": [{"type": "text", "value": "x"}],
    }


@pytest.mark.asyncio
async def test_taglist_multi_child_returns_list_through_transform() -> None:
    tl = TagList(tags.div("a"), tags.span("b"))

    @render_react
    def out():
        return tl

    result = await out.transform(tl)
    assert isinstance(result, list)
    assert [n["name"] for n in result] == ["div", "span"]


@pytest.mark.asyncio
async def test_render_time_dep_emits_warning() -> None:
    dep = HTMLDependency(name="d", version="1.0", source={"subdir": "/tmp"})
    node = Node(type="Card", props={}, children=[dep])

    @render_react
    def out():
        return node

    with pytest.warns(UserWarning, match="HTMLDependency"):
        await out.transform(node)


def test_auto_output_ui_returns_output_react() -> None:
    @render_react
    def my_card():
        return Node(type="Card", props={})

    rendered = str(my_card.auto_output_ui())
    assert "shinyreact-output" in rendered
    assert 'id="my_card"' in rendered
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest pkg-py/tests/test_render_react.py -q`
Expected: FAIL with `ImportError: cannot import name 'render_react'`.

- [ ] **Step 3: Create the `render_react` renderer**

Create `pkg-py/src/shinyreact/_render_react.py`:

```python
from __future__ import annotations

from htmltools import Tag, TagChild
from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._output import output_react
from ._render import walk_or_passthrough
from ._spec import Node


class render_react(Renderer["Node | TagChild"]):
    """Render a React component tree to a shinyreact output (the ``app.py`` pattern).

    Assign to ``output[id]`` where the UI has a matching ``output_react(id)``
    placeholder. Accepts a :class:`~shinyreact.Node` tree and any htmltools
    ``TagChild`` (``Tag``, ``TagList``, ``Tagifiable``, ``HTML``, scalar
    children) — walked into the JSON wire tree.

    Dependencies harvested from a walked tree cannot reach ``<head>`` after the
    page has rendered; declare them up-front via
    ``output_react(..., extra_deps=[...])`` or at the page level. A warning is
    emitted if a returned tree carries any.
    """

    async def transform(self, value: object) -> Jsonifiable:
        return walk_or_passthrough(value, self.output_id)

    def auto_output_ui(self) -> Tag:
        return output_react(self.output_id)
```

- [ ] **Step 4: Narrow `reactive_output` to the data case**

Replace the entire contents of `pkg-py/src/shinyreact/_reactive_output.py`:

```python
from __future__ import annotations

from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._render import walk_or_passthrough


class reactive_output(Renderer["Jsonifiable"]):
    """Publish a reactive JSON value to the client (the ``ui.tsx`` pattern).

    Assign to ``output[id]`` where a React client reads the value with
    ``useShinyOutputValue()``. There is no UI placeholder: ``auto_output_ui()``
    inherits the base implementation, which returns ``None``.

    Accepts any JSON-serializable value (``dict``, ``list``, ``str``, ``int``,
    ``float``, ``bool``, ``None``), passed through unchanged.
    """

    async def transform(self, value: object) -> Jsonifiable:
        return walk_or_passthrough(value, self.output_id)
```

- [ ] **Step 5: Update package exports**

Replace `pkg-py/src/shinyreact/__init__.py`:

```python
from ._output import output_react
from ._page import page_bare, page_react, page_react_dep, set_react_page
from ._reactive_output import reactive_output
from ._render_react import render_react
from ._send_message import send_message
from ._spec import Node

__all__ = [
    "Node",
    "output_react",
    "page_bare",
    "page_react",
    "page_react_dep",
    "reactive_output",
    "render_react",
    "send_message",
    "set_react_page",
]
```

- [ ] **Step 6: Rewrite `test_reactive_output.py` for the data-only contract**

Replace the entire contents of `pkg-py/tests/test_reactive_output.py`:

```python
"""Tests for reactive_output (ui.tsx pattern: publishes JSON data, no placeholder)."""

from __future__ import annotations

import pytest
from shinyreact import reactive_output


@pytest.mark.asyncio
async def test_passthrough_dict() -> None:
    @reactive_output
    def out():
        return {"a": 1, "b": [2, 3]}

    assert await out.transform({"a": 1, "b": [2, 3]}) == {"a": 1, "b": [2, 3]}


@pytest.mark.asyncio
async def test_passthrough_primitive() -> None:
    @reactive_output
    def out():
        return 42

    assert await out.transform(42) == 42


@pytest.mark.asyncio
async def test_passthrough_string_is_json_not_text_node() -> None:
    @reactive_output
    def out():
        return "hello"

    # Top-level str is JSON passthrough, NOT a {"type": "text"} node.
    assert await out.transform("hello") == "hello"


@pytest.mark.asyncio
async def test_passthrough_list() -> None:
    @reactive_output
    def out():
        return [1, 2, 3]

    assert await out.transform([1, 2, 3]) == [1, 2, 3]


@pytest.mark.asyncio
async def test_passthrough_none() -> None:
    @reactive_output
    def out():
        return None

    assert await out.transform(None) is None


def test_auto_output_ui_returns_none() -> None:
    @reactive_output
    def my_value():
        return {"x": 1}

    assert my_value.auto_output_ui() is None


def test_no_extra_deps_attribute() -> None:
    assert not hasattr(reactive_output, "extra_deps")
```

- [ ] **Step 7: Run all affected tests**

Run: `uv run pytest pkg-py/tests/test_render_react.py pkg-py/tests/test_reactive_output.py -q`
Expected: PASS (all tests in both files).

- [ ] **Step 8: Run the type checker**

Run: `make py-check-types`
Expected: pyright reports no errors.

- [ ] **Step 9: Commit**

```bash
git add pkg-py/src/shinyreact/_render_react.py pkg-py/src/shinyreact/_reactive_output.py pkg-py/src/shinyreact/__init__.py pkg-py/tests/test_render_react.py pkg-py/tests/test_reactive_output.py
git commit -m "feat(py): add render_react, narrow reactive_output to data"
```

---

## Task 4: Python — migrate `app-py` examples to `render_react` + `output_react`

**Files:**
- Modify: every `examples/app-py/*/app.py` that references `ui_output` or `reactive_output`
- Modify: `examples/app-py/*/README.md` that reference these names

App-pattern examples: `ui_output(` → `output_react(`, and `reactive_output` (decorator/base class) → `render_react`. This covers `01-hello-world`, `02-inputs`, `03-outputs`, `04-messages`, `05-shadcn`, `06-dashboard`, `07-chat`, `08-modules`, `09-blended`, `11-hello-spa-old`, `12-express-demo`, `13-bookmarking`, `14-nesting`.

- [ ] **Step 1: Edit the app files**

In each `examples/app-py/*/app.py`: replace `shinyreact.ui_output` → `shinyreact.output_react`, bare `ui_output(` → `output_react(`, `shinyreact.reactive_output` → `shinyreact.render_react`, and bare `@reactive_output` / `reactive_output)` → `render_react`. Update any `from shinyreact import ... reactive_output ... ui_output ...` import lines to `render_react` / `output_react`.

For `examples/app-py/05-shadcn` (downstream-style `class render(shinyreact.reactive_output)`): change the base class to `shinyreact.render_react`.

- [ ] **Step 2: Edit the example READMEs**

In each `examples/app-py/*/README.md`, replace `ui_output` → `output_react` and `reactive_output` → `render_react`.

- [ ] **Step 3: Verify no stale names remain in app-py**

Run: `rg -n 'ui_output\b|reactive_output' examples/app-py`
Expected: no matches.

- [ ] **Step 4: Smoke-test a representative app imports**

Run: `uv run python -c "import runpy, sys; sys.argv=['app']; runpy.run_path('examples/app-py/03-outputs/app.py')" 2>&1 | head -5`
Expected: no `ImportError`/`AttributeError` for `output_react`/`render_react` (a Shiny "App object" or running-context message is fine; the goal is that the names resolve).

- [ ] **Step 5: Commit**

```bash
git add examples/app-py
git commit -m "docs(examples): migrate app-py to output_react/render_react"
```

---

## Task 5: Python — confirm `ui-tsx` examples use `reactive_output`

**Files:**
- Modify (if needed): `examples/ui-tsx/*/app.py`, `examples/ui-tsx/*/README.md`

These are ui.tsx-pattern (no placeholder; values read by hooks). They should keep `reactive_output` and must not use `ui_output`/`output_react`. Covers `01-hello`, `02-columns`, `03-columns-shadcn`, `04-shadcn`, `05-temperature`, `06-data-frame`, `07-plotly`, `08-input-handler`.

- [ ] **Step 1: Check for any placeholder usage to fix**

Run: `rg -n 'ui_output|output_react|render_react' examples/ui-tsx`
Expected: ideally no matches (these examples use `reactive_output` only). If any `ui_output` appears, change it to `output_react`; if any `render_react` appears on a hook-read output, change it to `reactive_output`.

- [ ] **Step 2: Verify `reactive_output` references are intact**

Run: `rg -n 'reactive_output' examples/ui-tsx | head`
Expected: matches present and unchanged (e.g. `05-temperature`, `01-hello`).

- [ ] **Step 3: Commit (only if edits were made)**

```bash
git add examples/ui-tsx
git commit -m "docs(examples): align ui-tsx output helpers with reactive_output"
```

If `git status` shows no changes, skip the commit.

---

## Task 6: Python — migrate playwright fixture apps and tests

**Files:**
- Modify: `pkg-py/tests/playwright/apps/nesting/app.py`, `pkg-py/tests/playwright/apps/input-handler-type/app.py`, `pkg-py/tests/playwright/apps/classname/app.py`, `pkg-py/tests/playwright/apps/bookmark/app.py`
- Modify: `pkg-py/tests/playwright/test_nesting.py`
- Modify: `pkg-py/tests/test_set_react_page.py`, `pkg-py/tests/test_bookmark_restore.py`

- [ ] **Step 1: Edit fixture apps per the migration rule**

For each fixture `app.py`: if it builds UI into a placeholder (app pattern — uses `ui_output` / `page_react`), change `ui_output(` → `output_react(` and `reactive_output` → `render_react`. If it is ui.tsx-pattern (uses `set_react_page`, value read by hook), keep `reactive_output` and only rename any `ui_output` → `output_react`. Inspect each before editing — `nesting`, `classname` are app-pattern (→ `render_react`); `bookmark`, `input-handler-type` should be checked individually.

- [ ] **Step 2: Edit the Python test files**

In `pkg-py/tests/test_set_react_page.py` and `pkg-py/tests/test_bookmark_restore.py`, replace any `ui_output` → `output_react` and `reactive_output` → `render_react` / `reactive_output` per the same rule (these import or reference the renderer/placeholder). In `pkg-py/tests/playwright/test_nesting.py`, update any references to the renamed symbols.

- [ ] **Step 3: Verify no stale names**

Run: `rg -n 'ui_output\b' pkg-py/tests`
Expected: no matches.

- [ ] **Step 4: Run the non-e2e Python suite**

Run: `make py-check-tests`
Expected: PASS.

- [ ] **Step 5: Run the e2e suite**

Run: `make py-test-e2e`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pkg-py/tests
git commit -m "test(py): migrate playwright fixtures and tests to new names"
```

---

## Task 7: R — rename `ui_output_react` → `output_react`

**Files:**
- Modify: `pkg-r/R/output.R`
- Test: `pkg-r/tests/testthat/test-ui-output.R`

- [ ] **Step 1: Update the test file**

In `pkg-r/tests/testthat/test-ui-output.R`, replace every `ui_output_react(` with `output_react(` and update the two `test_that` descriptions from `ui_output_react()` to `output_react()`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-ui-output.R")'`
Expected: FAIL — `could not find function "output_react"`.

- [ ] **Step 3: Rename the function in source**

In `pkg-r/R/output.R`, rename `ui_output_react` → `output_react` and update the roxygen title/`@param` to reference `render_react()`:

```r
#' Output placeholder for a shinyreact renderer
#'
#' Creates the `<div>` that the shinyreact Shiny output binding renders into.
#' Pair with [render_react()] on the server (assign to `output[[id]]`).
#'
#' @param id Output ID. Must match the server-side `output[[id]]` assignment.
#' @param extra_deps A list of [htmltools::htmlDependency] objects to include.
#'   Downstream packages use this to inject their own JS/CSS.
#' @return A `shiny.tag` `<div>`.
#' @export
output_react <- function(id, extra_deps = list()) {
  htmltools::div(
    id = id,
    class = "shinyreact-output",
    shinyreact_dep(),
    extra_deps
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-ui-output.R")'`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pkg-r/R/output.R pkg-r/tests/testthat/test-ui-output.R
git commit -m "refactor(r): rename ui_output_react -> output_react"
```

---

## Task 8: R — add `reactive_output`, point `render_react` at `output_react`

**Files:**
- Modify: `pkg-r/R/render.R`
- Test: `pkg-r/tests/testthat/test-render.R`

- [ ] **Step 1: Write the failing test for `reactive_output`**

Append to `pkg-r/tests/testthat/test-render.R`:

```r
test_that("reactive_output returns a shiny render function", {
  r <- reactive_output(list(a = 1, b = 2))
  expect_s3_class(r, "shiny.render.function")
})

test_that("reactive_output passes data through .render_transform", {
  expect_identical(
    shinyreact:::.render_transform(list(key = "value", count = 42L)),
    list(key = "value", count = 42L)
  )
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-render.R")'`
Expected: FAIL — `could not find function "reactive_output"`.

- [ ] **Step 3: Update `render_react`'s default UI and add `reactive_output`**

In `pkg-r/R/render.R`: (a) change the warning message in `.render_transform` to reference `output_react`, (b) change `render_react`'s `createRenderFunction` third argument from `ui_output_react` to `output_react`, and (c) add `reactive_output` below `render_react`.

Change the warning hint line in `.render_transform`:

```r
        "i" = "Declare them up-front via {.code output_react(..., extra_deps = list(...))} or at the page level."
```

Change the `render_react` body's render-function creation:

```r
  shiny::createRenderFunction(
    func,
    function(value, session, name, ...) .render_transform(value),
    output_react
  )
```

Add the new function after `render_react`:

```r
#' Publish a reactive value to a shinyreact client (the `ui.tsx` pattern)
#'
#' Server-side counterpart to `useShinyOutputValue()`. Assign to `output[[id]]`;
#' a React client reads the value by id. Unlike [render_react()] there is no UI
#' placeholder — the client owns all UI. Accepts any JSON-serializable value
#' (passed through unchanged).
#'
#' @param expr An expression returning a JSON-serializable value.
#' @param env The environment in which to evaluate `expr`.
#' @param quoted Is `expr` already quoted?
#' @return A Shiny render function.
#' @export
reactive_output <- function(expr, env = parent.frame(), quoted = FALSE) {
  func <- shiny::installExprFunction(
    expr,
    "func",
    eval.env = env,
    quoted = quoted,
    label = "reactive_output"
  )
  shiny::createRenderFunction(
    func,
    function(value, session, name, ...) .render_transform(value)
  )
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-render.R")'`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pkg-r/R/render.R pkg-r/tests/testthat/test-render.R
git commit -m "feat(r): add reactive_output; render_react default UI -> output_react"
```

---

## Task 9: R — regenerate NAMESPACE, man pages, and `_pkgdown.yml`

**Files:**
- Modify (generated): `pkg-r/NAMESPACE`, `pkg-r/man/*.Rd`
- Modify: `pkg-r/_pkgdown.yml`

- [ ] **Step 1: Regenerate roxygen docs and NAMESPACE**

Run: `cd pkg-r && Rscript -e 'roxygen2::roxygenise()'`
Expected: `NAMESPACE` now has `export(output_react)` and `export(reactive_output)` and no `export(ui_output_react)`; `man/output_react.Rd` and `man/reactive_output.Rd` exist.

- [ ] **Step 2: Remove the stale man page if not auto-removed**

Run: `git status pkg-r/man`
If `man/ui_output_react.Rd` still exists, delete it: `git rm pkg-r/man/ui_output_react.Rd`.

- [ ] **Step 3: Update `_pkgdown.yml`**

In `pkg-r/_pkgdown.yml`, replace `ui_output_react` → `output_react` and add `reactive_output` to the same reference section that lists `render_react`.

- [ ] **Step 4: Verify no stale names remain in the package**

Run: `rg -n 'ui_output_react' pkg-r`
Expected: no matches.

- [ ] **Step 5: Commit**

```bash
git add pkg-r/NAMESPACE pkg-r/man pkg-r/_pkgdown.yml
git commit -m "docs(r): regenerate man/NAMESPACE/_pkgdown for renderer split"
```

---

## Task 10: R — migrate `app-r` and `ui-tsx-r` examples

**Files:**
- Modify: `examples/app-r/01-hello-world/app.R`, `examples/app-r/02-inputs/app.R`, `examples/app-r/04-messages/app.R`, `examples/app-r/02-inputs/README.md`
- Modify: `examples/ui-tsx-r/01-hello/app.R`, `examples/ui-tsx-r/01-hello/README.md`

- [ ] **Step 1: Migrate the app-r examples (app pattern)**

In each `examples/app-r/*/app.R` and `examples/app-r/02-inputs/README.md`: replace `ui_output_react(` → `output_react(`. Leave `render_react` as-is (app pattern keeps it).

- [ ] **Step 2: Migrate the ui-tsx-r example (ui.tsx pattern)**

In `examples/ui-tsx-r/01-hello/app.R` and its `README.md`: replace `render_react(` → `reactive_output(` (these outputs are read by hooks with no placeholder).

- [ ] **Step 3: Verify**

Run: `rg -n 'ui_output_react' examples/app-r examples/ui-tsx-r; rg -n 'render_react' examples/ui-tsx-r`
Expected: no matches for either.

- [ ] **Step 4: Commit**

```bash
git add examples/app-r examples/ui-tsx-r
git commit -m "docs(examples): migrate R examples to output_react/reactive_output"
```

---

## Task 11: Update current documentation

**Files:**
- Modify: `README.md`, `pkg-py/README.md`, `pkg-r/README.md`, `CLAUDE.md`, `DESIGN.md`, `docs/features.md`, `docs/app-py-vs-ui-tsx.md`, `docs/todos.md`, `docs/timeline.md`, `.claude/references/playwright-e2e-tests.md`

Do **not** touch `docs/superpowers/specs/*`, `docs/superpowers/plans/*` (except this plan), or `decisions/*` — those are historical records.

- [ ] **Step 1: Sweep the docs, applying the pattern rule**

For each file, apply: `ui_output`/`ui_output_react` → `output_react`. For `reactive_output`/`render_react` mentions, set the name by the pattern being described — app pattern (paired with `output_react`, `page_react`) → `render_react`; ui.tsx pattern (`set_react_page`, hooks) → `reactive_output`. In `CLAUDE.md` specifically: the "Action buttons" Python snippet and the "Downstream package pattern" (`class render(shinyreact.reactive_output)`) describe the app pattern → use `render_react`; update the "Python package" bullet list to document both `render_react` (app, with `output_react`) and `reactive_output` (ui.tsx, data-only, no placeholder). Update `docs/features.md` tables to list both renderers and `output_react`.

- [ ] **Step 2: Verify no stale names remain in current docs**

Run: `rg -n 'ui_output\b|ui_output_react' README.md pkg-py/README.md pkg-r/README.md CLAUDE.md DESIGN.md docs/features.md docs/app-py-vs-ui-tsx.md docs/todos.md docs/timeline.md .claude/references/playwright-e2e-tests.md`
Expected: no matches.

- [ ] **Step 3: Commit**

```bash
git add README.md pkg-py/README.md pkg-r/README.md CLAUDE.md DESIGN.md docs/features.md docs/app-py-vs-ui-tsx.md docs/todos.md docs/timeline.md .claude/references/playwright-e2e-tests.md
git commit -m "docs: document render_react/reactive_output split and output_react"
```

---

## Task 12: Full verification sweep

**Files:** none (verification only)

- [ ] **Step 1: Confirm no stale public names remain anywhere outside historical records**

Run: `rg -n 'ui_output\b|ui_output_react' --glob '!docs/superpowers/**' --glob '!decisions/**'`
Expected: no matches.

- [ ] **Step 2: Run the full Python checks**

Run: `make py-check`
Expected: format check, pyright, and pytest all PASS.

- [ ] **Step 3: Run the Python e2e suite**

Run: `make py-test-e2e`
Expected: PASS.

- [ ] **Step 4: Run the full R checks**

Run: `make r-check`
Expected: format, tests, and `R CMD check` all PASS.

- [ ] **Step 5: Final commit if `make` reformatted anything**

```bash
git add -A
git commit -m "chore: formatting after renderer split" || echo "nothing to commit"
```
