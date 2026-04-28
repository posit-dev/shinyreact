# shinyjson SPA-First Split — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the existing `shinyjson` Python package to `shinyjsonold` and create a new parallel `shinyjson` package implementing the minimal SPA-first server primitives (`SpaApp`, `render_json`).

**Architecture:** Two packages ship from one wheel. `shinyjsonold/` is a verbatim rename of today's `shinyjson/` (all internal imports + HTMLDependency name updated). New `shinyjson/` exposes only `SpaApp` (lifts `examples/10-spa-hello/spa_app.py` into the package) and `render_json` (a `Renderer[Jsonifiable]` that passes JSON through unchanged). New `shinyjson/www/` is a byte-identical copy of the old bundle.

**Tech Stack:** Python 3.10+, hatchling build backend, Shiny for Python, htmltools.

**Spec:** `docs/superpowers/specs/2026-04-28-shinyjson-spa-split-design.md`

---

## Task 1: Rename `pkg-py/src/shinyjson/` → `pkg-py/src/shinyjsonold/`

**Files:**
- Move directory: `pkg-py/src/shinyjson/` → `pkg-py/src/shinyjsonold/`

- [ ] **Step 1: Move the directory with `git mv`**

```bash
git mv pkg-py/src/shinyjson pkg-py/src/shinyjsonold
```

- [ ] **Step 2: Verify move**

Run: `ls pkg-py/src/`
Expected: shows `shinyjsonold/` and no `shinyjson/`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: rename shinyjson package directory to shinyjsonold"
```

---

## Task 2: Update `shinyjsonold` internals (HTMLDependency name only)

The CSS class `shinyjson-output` and the JS `window.shinyjson` global stay unchanged (the JS bundle is shared between both packages). Only the HTMLDependency `name` field is updated so the dependency does not collide with the new package's `shinyjson` HTMLDependency name.

**Files:**
- Modify: `pkg-py/src/shinyjsonold/_output.py`

- [ ] **Step 1: Update HTMLDependency name in `_output.py`**

Change the `name` argument of `HTMLDependency(...)` in `_dep()`:

```python
def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyjsonold",
        version="0.1.0",
        source={"subdir": str(Path(__file__).parent / "www")},
        script={"src": "shinyjson.js", "defer": ""},
        stylesheet={"href": "shinyjson.css"},
    )
```

- [ ] **Step 2: Verify no other internal references to `name="shinyjson"` HTMLDependency**

Run: `grep -rn 'name="shinyjson"' pkg-py/src/shinyjsonold/`
Expected: no output

- [ ] **Step 3: Commit**

```bash
git add pkg-py/src/shinyjsonold/_output.py
git commit -m "refactor: rename shinyjsonold HTMLDependency to avoid collision with new shinyjson"
```

---

## Task 3: Update `pyproject.toml` to ship `shinyjsonold`

The wheel currently exposes `shinyjson`. Until the new `shinyjson/` directory exists (Task 5), the wheel only contains `shinyjsonold/`. Tests in this task confirm the rename works end-to-end before we add the new package.

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update `[tool.hatch.build.targets.wheel]` and `[tool.pyright]`**

Replace:

```toml
[tool.hatch.build.targets.wheel]
packages = ["pkg-py/src/shinyjson"]
```

with:

```toml
[tool.hatch.build.targets.wheel]
packages = ["pkg-py/src/shinyjsonold"]
```

Replace:

```toml
[tool.pyright]
include = ["pkg-py/src/shinyjson"]
pythonVersion = "3.10"
typeCheckingMode = "basic"
```

with:

```toml
[tool.pyright]
include = ["pkg-py/src/shinyjsonold"]
pythonVersion = "3.10"
typeCheckingMode = "basic"
```

- [ ] **Step 2: Re-sync the environment**

Run: `uv sync --all-extras --all-groups`
Expected: succeeds; the `shinyjsonold` package is now importable.

- [ ] **Step 3: Sanity-check import**

Run: `uv run python -c "import shinyjsonold; print(shinyjsonold.__all__)"`
Expected: prints the package's `__all__` list (no `ImportError`).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "build: point hatchling and pyright at shinyjsonold"
```

---

## Task 4: Update tests + existing examples to import `shinyjsonold`

This task is a mechanical search-and-replace across `pkg-py/tests/` and `examples/` (excluding the not-yet-created `examples/13-spa-hello/`).

**Files:**
- Modify: `pkg-py/tests/test_spec.py`, `pkg-py/tests/test_render.py`, `pkg-py/tests/test_post_message.py`, `pkg-py/tests/test_page.py`, `pkg-py/tests/test_output.py`
- Modify: `examples/1-hello-world/app.py`, `examples/2-inputs/app.py`, `examples/3-outputs/app.py`, `examples/4-messages/app.py`, `examples/5-shadcn/app.py`, `examples/6-dashboard/app.py`, `examples/7-chat/app.py`, `examples/8-modules/app.py`, `examples/9-blended/app.py`, `examples/10-spa-hello/app.py`, `examples/12-columns-spa/app.py`, `examples/hello-shinyjson/app.py`

- [ ] **Step 1: Replace `import shinyjson` and `from shinyjson` references in tests**

For each test file, replace any `import shinyjson` with `import shinyjsonold as shinyjson` (preserving the `shinyjson.` symbol prefix in test bodies — minimizes diff and keeps tests readable). For any `from shinyjson import X`, change to `from shinyjsonold import X`.

Use `sed` per file or do the equivalent with the `Edit` tool. Example:

```bash
# Verify a test file's shinyjson references first
grep -n shinyjson pkg-py/tests/test_spec.py
```

Then perform the rewrite. Repeat for all five test files.

- [ ] **Step 2: Replace `import shinyjson` references in examples (1–9, 11, 12, hello-shinyjson)**

Examples currently say `import shinyjson` (and may also say `from shinyjson import ...`). Rewrite to `import shinyjsonold as shinyjson` (and `from shinyjsonold import ...`). Apply to each example listed in the **Files** section above.

Note: `examples/11-columns-traditional/app.py` does **not** import shinyjson per the grep results — skip it.

- [ ] **Step 3: Run the Python test suite**

Run: `make py-check-tests`
Expected: PASS — the same tests that passed before the rename still pass.

- [ ] **Step 4: Run pyright**

Run: `make py-check-types`
Expected: PASS.

- [ ] **Step 5: Run formatter check**

Run: `make py-format`
Expected: no changes needed.

- [ ] **Step 6: Commit**

```bash
git add pkg-py/tests/ examples/
git commit -m "refactor: update tests and examples to import shinyjsonold"
```

---

## Task 5: Create new `shinyjson` package skeleton

Creates the new package directory with `__init__.py` and copies the JS bundle. `SpaApp` and `render_json` are added in subsequent tasks.

**Files:**
- Create: `pkg-py/src/shinyjson/__init__.py`
- Create: `pkg-py/src/shinyjson/www/` (copy of `pkg-py/src/shinyjsonold/www/`)

- [ ] **Step 1: Create the package directory and copy the JS bundle**

```bash
mkdir -p pkg-py/src/shinyjson
cp -R pkg-py/src/shinyjsonold/www pkg-py/src/shinyjson/www
```

- [ ] **Step 2: Create empty `__init__.py`**

Write `pkg-py/src/shinyjson/__init__.py`:

```python
__all__: list[str] = []
```

- [ ] **Step 3: Add the new package to hatchling and pyright config**

Edit `pyproject.toml`. Replace:

```toml
[tool.hatch.build.targets.wheel]
packages = ["pkg-py/src/shinyjsonold"]
```

with:

```toml
[tool.hatch.build.targets.wheel]
packages = ["pkg-py/src/shinyjson", "pkg-py/src/shinyjsonold"]
```

Replace:

```toml
[tool.pyright]
include = ["pkg-py/src/shinyjsonold"]
```

with:

```toml
[tool.pyright]
include = ["pkg-py/src/shinyjson", "pkg-py/src/shinyjsonold"]
```

- [ ] **Step 4: Re-sync and sanity-check both imports**

```bash
uv sync --all-extras --all-groups
uv run python -c "import shinyjson, shinyjsonold; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyjson/ pyproject.toml
git commit -m "feat: scaffold new shinyjson package with bundled JS"
```

---

## Task 6: Implement `SpaApp` in new `shinyjson` package

`SpaApp` reads `index.html` from the supplied `www_dir`, wraps it in `TagList(HTML(...))` so Shiny still injects its runtime, and serves the directory as static assets. It also attaches the `shinyjson` HTMLDependency so the bridge JS loads.

**Files:**
- Create: `pkg-py/src/shinyjson/_spa_app.py`
- Create: `pkg-py/tests/new/__init__.py`
- Create: `pkg-py/tests/new/test_spa_app.py`
- Modify: `pkg-py/src/shinyjson/__init__.py`

- [ ] **Step 1: Create `pkg-py/tests/new/__init__.py` (empty)**

Write `pkg-py/tests/new/__init__.py`:

```python
```

(Empty file — marks the directory as a test package to keep new package tests separate from `shinyjsonold` tests.)

- [ ] **Step 2: Write the failing test**

Write `pkg-py/tests/new/test_spa_app.py`:

```python
from pathlib import Path

from shiny import App

import shinyjson


def test_spa_app_subclasses_shiny_app(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html><body><div id='root'></div></body></html>")

    def server(input, output, session):  # noqa: ARG001
        return None

    app = shinyjson.SpaApp(tmp_path, server)
    assert isinstance(app, App)


def test_spa_app_reads_index_html(tmp_path: Path) -> None:
    marker = "<!-- spa-app-test-marker -->"
    (tmp_path / "index.html").write_text(
        f"<html><body>{marker}<div id='root'></div></body></html>"
    )

    def server(input, output, session):  # noqa: ARG001
        return None

    app = shinyjson.SpaApp(tmp_path, server)
    rendered = str(app.ui)
    assert marker in rendered
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest pkg-py/tests/new/test_spa_app.py -v`
Expected: FAIL with `AttributeError: module 'shinyjson' has no attribute 'SpaApp'`.

- [ ] **Step 4: Implement `SpaApp`**

Write `pkg-py/src/shinyjson/_spa_app.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Callable

from htmltools import HTML, HTMLDependency, TagList
from shiny import App
from shiny.session import Inputs, Outputs, Session


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyjson",
        version="0.1.0",
        source={"subdir": str(Path(__file__).parent / "www")},
        script={"src": "shinyjson.js", "defer": ""},
        stylesheet={"href": "shinyjson.css"},
    )


class SpaApp(App):
    """A Shiny app that serves a static SPA from a ``www/`` directory.

    The ``www_dir`` must contain an ``index.html`` file. All files in
    ``www_dir`` are served as static assets. The server function contains only
    reactive computation and business logic — no UI definitions.

    Args:
        www_dir: Path to the directory containing ``index.html`` and static
            assets. Typically ``Path(__file__).parent / "www"``.
        server: The Shiny server function.
    """

    def __init__(
        self,
        www_dir: str | Path,
        server: Callable[[Inputs, Outputs, Session], None],
        **kwargs: object,
    ) -> None:
        www_dir = Path(www_dir)
        ui = TagList(
            _dep(),
            HTML((www_dir / "index.html").read_text()),
        )
        super().__init__(ui, server, static_assets=www_dir, **kwargs)
```

- [ ] **Step 5: Export `SpaApp` from `__init__.py`**

Replace `pkg-py/src/shinyjson/__init__.py` with:

```python
from ._spa_app import SpaApp

__all__ = ["SpaApp"]
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `uv run pytest pkg-py/tests/new/test_spa_app.py -v`
Expected: PASS (both test functions).

- [ ] **Step 7: Commit**

```bash
git add pkg-py/src/shinyjson/ pkg-py/tests/new/
git commit -m "feat: add SpaApp to new shinyjson package"
```

---

## Task 7: Implement `render_json` in new `shinyjson` package

`render_json` is a `Renderer[Jsonifiable]` whose `transform` returns the value unchanged. There is no `Spec`/`Node` handling and no `extra_deps` hook (per Tenet 4 — no dynamic dependency injection in SPA-first apps).

**Files:**
- Create: `pkg-py/src/shinyjson/_render_json.py`
- Create: `pkg-py/tests/new/test_render_json.py`
- Modify: `pkg-py/src/shinyjson/__init__.py`

- [ ] **Step 1: Write the failing test**

Write `pkg-py/tests/new/test_render_json.py`:

```python
import pytest

import shinyjson


@pytest.mark.asyncio
async def test_render_json_passes_dict_through() -> None:
    @shinyjson.render_json
    def my_data():
        return {"title": "Hello", "count": 42}

    result = await my_data.transform({"title": "Hello", "count": 42})
    assert result == {"title": "Hello", "count": 42}


@pytest.mark.asyncio
async def test_render_json_passes_primitives_through() -> None:
    @shinyjson.render_json
    def my_data():
        return 42

    assert await my_data.transform(42) == 42
    assert await my_data.transform("hello") == "hello"
    assert await my_data.transform(None) is None
    assert await my_data.transform([1, 2, 3]) == [1, 2, 3]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest pkg-py/tests/new/test_render_json.py -v`
Expected: FAIL with `AttributeError: module 'shinyjson' has no attribute 'render_json'`.

- [ ] **Step 3: Implement `render_json`**

Write `pkg-py/src/shinyjson/_render_json.py`:

```python
from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable


class render_json(Renderer[Jsonifiable]):
    """Send a JSON-serializable value to the client.

    Use on a server function whose return value is consumed by a
    ``useShinyOutput()`` hook on the client. The value is passed through
    unchanged — no transformation, no UI generation.

    Example::

        @shinyjson.render_json
        def my_data():
            return {"title": "Hello", "count": 42}
    """

    async def transform(self, value: Jsonifiable) -> Jsonifiable:
        return value
```

- [ ] **Step 4: Export `render_json` from `__init__.py`**

Replace `pkg-py/src/shinyjson/__init__.py` with:

```python
from ._render_json import render_json
from ._spa_app import SpaApp

__all__ = ["SpaApp", "render_json"]
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest pkg-py/tests/new/test_render_json.py -v`
Expected: PASS (both test functions).

- [ ] **Step 6: Run the full Python test suite**

Run: `make py-check`
Expected: PASS (formatting, types, all tests).

- [ ] **Step 7: Commit**

```bash
git add pkg-py/src/shinyjson/ pkg-py/tests/new/
git commit -m "feat: add render_json renderer to new shinyjson package"
```

---

## Task 8: Create `examples/13-spa-hello/` using the new package

A clone of `examples/10-spa-hello/` with the local `spa_app.py` removed and `app.py` rewritten to use the new package.

**Files:**
- Create: `examples/13-spa-hello/.gitignore`
- Create: `examples/13-spa-hello/package.json`
- Create: `examples/13-spa-hello/app.py`
- Create: `examples/13-spa-hello/src/index.html`
- Create: `examples/13-spa-hello/src/index.jsx`
- Create: `examples/13-spa-hello/src/App.jsx`
- Create: `examples/13-spa-hello/src/react-shim.js`
- Create: `examples/13-spa-hello/www/main.css`
- Create: `examples/13-spa-hello/www/shinyjson.css`
- Create: `examples/13-spa-hello/www/shinyjson.js`
- (Note: do NOT commit a hashed `index-XXXXX.js` or generated `www/index.html` — those come from the build.)

- [ ] **Step 1: Copy the directory tree from example 10**

```bash
cp -R examples/10-spa-hello examples/13-spa-hello
rm examples/13-spa-hello/spa_app.py
rm examples/13-spa-hello/app-old.txt
rm -f examples/13-spa-hello/www/index-*.js
rm -f examples/13-spa-hello/www/index.html
```

- [ ] **Step 2: Rewrite `examples/13-spa-hello/app.py`**

Replace contents with:

```python
from pathlib import Path

import shinyjson
from shiny import reactive

_src_dir = Path(__file__).parent


def server(input, output, session):  # noqa: ARG001
    @reactive.calc
    def greeting():
        name = input.name()
        if not name:
            return "World"
        return name

    @shinyjson.render_json
    def txtout_title():
        return f"Hello, {greeting()}!"

    @shinyjson.render_json
    def txtout_count():
        return input.click_count()


app = shinyjson.SpaApp(_src_dir / "www", server)
```

- [ ] **Step 3: Build the SPA bundle**

```bash
cd examples/13-spa-hello && npm install && npm run build && cd -
```

Expected: prints `Built: index-<HASH>.js` and creates `www/index-<HASH>.js` and `www/index.html`. Note these are NOT committed (covered by `.gitignore`).

- [ ] **Step 4: Verify the .gitignore covers built artifacts**

Run: `cat examples/13-spa-hello/.gitignore`
Expected: matches example 10's `.gitignore` (e.g., ignores `node_modules/`, `www/index-*.js`, `www/index.html`).

If it does not, edit it to match `examples/10-spa-hello/.gitignore`.

- [ ] **Step 5: Smoke-test the app**

Run (in foreground, kill after a few seconds):

```bash
uv run shiny run examples/13-spa-hello/app.py --port 8765 &
SHINY_PID=$!
sleep 3
curl -fs http://127.0.0.1:8765/ | head -20
kill $SHINY_PID
```

Expected: the curl output contains the contents of the built `index.html` (a `<div id="root">` and a `<script>` tag referencing the hashed JS bundle).

- [ ] **Step 6: Commit**

```bash
git add examples/13-spa-hello/
git commit -m "feat: add examples/13-spa-hello demonstrating new SPA-first shinyjson"
```

---

## Task 9: Update `docs/STATUS.md` and `CLAUDE.md`

A one-paragraph note explaining the parallel packages and pointing future contributors at the spec.

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add a "Parallel packages" note to `docs/STATUS.md`**

Add a section (near the top, after the title) with the following content:

```markdown
## Parallel packages: `shinyjson` (SPA-first) and `shinyjsonold` (JSON-spec)

The original `shinyjson` package — server-driven UI via JSON specs and
`@json-render/react` — has been renamed to **`shinyjsonold`**. A new,
minimal `shinyjson` package now sits alongside it implementing the
SPA-first server primitives from `DESIGN.md`: `SpaApp` and `render_json`.

- Existing examples (1–12) and tests use `shinyjsonold`.
- `examples/13-spa-hello/` demonstrates the new `shinyjson`.

See `docs/superpowers/specs/2026-04-28-shinyjson-spa-split-design.md` for
the rationale and scope.
```

- [ ] **Step 2: Update `CLAUDE.md` "Repo structure" section**

Replace the line `pkg-py/                     # Python package` block with one that lists both packages, e.g.:

```
pkg-py/                         # Python packages
  src/shinyjson/                # NEW SPA-first package: SpaApp, render_json
    www/                        # Bundled JS
  src/shinyjsonold/             # Original JSON-spec package
    _spec.py, _output.py, _render.py, _post_message.py, _page_react.py, www/
  tests/                        # pytest tests for shinyjsonold
  tests/new/                    # pytest tests for new shinyjson
```

Add one sentence near the top of CLAUDE.md noting the parallel packages exist
and pointing at `DESIGN.md` and the spec.

- [ ] **Step 3: Commit**

```bash
git add docs/STATUS.md CLAUDE.md
git commit -m "docs: note parallel shinyjson + shinyjsonold packages"
```

---

## Task 10: Final verification

- [ ] **Step 1: Run full check**

```bash
make py-check
```

Expected: PASS.

- [ ] **Step 2: Verify both packages import cleanly**

```bash
uv run python -c "import shinyjson, shinyjsonold; print(shinyjson.__all__); print(shinyjsonold.__all__)"
```

Expected: prints `['SpaApp', 'render_json']` and the original `shinyjsonold` `__all__` list.

- [ ] **Step 3: Verify no dangling `import shinyjson` outside the new package or example 13**

Run: `grep -rn "import shinyjson" pkg-py/ examples/ | grep -v shinyjsonold | grep -v "examples/13-spa-hello"`
Expected: no output (every other reference now uses `shinyjsonold`).
