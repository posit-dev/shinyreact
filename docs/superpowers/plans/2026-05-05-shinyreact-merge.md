# shinyreact merge: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `shinyjson` (SPA-first) and `shinyjsonold` (JSON-spec) with a single package `shinyreact` that ships both patterns, per `docs/superpowers/specs/2026-05-05-shinyreact-merge-design.md`.

**Architecture:** Build a new `pkg-py/src/shinyreact/` by porting modules from the two old packages. Replace `render_json` + `render` with a single unified `reactive_output` decorator (`Spec | Node | Jsonifiable`, no `extra_deps`, keeps `auto_output_ui()`). Replace `post_message` + `send_json` with one `send_message`. Rename JS globals (`window.shinyjson` → `window.shinyreact`), CSS class (`shinyjson-output` → `shinyreact-output`), HTMLDependency name, and bundle filename. Delete both old packages. Reorganize examples into `examples/traditional/` and `examples/spa/`.

**Tech Stack:** Python 3.10+, Shiny, htmltools, hatchling. TypeScript / React 19 / Vite IIFE. pytest, ruff, pyright.

---

## File structure (target)

```
pkg-py/src/shinyreact/
  __init__.py             # exports SpaApp, page_react, page_bare, page_react_dep,
                          # ui_output, reactive_output, send_message, Spec, Node, Element
  _spec.py                # Spec, Node, Element (from shinyjsonold)
  _output.py              # ui_output + _dep() (HTMLDependency name "shinyreact")
  _page.py                # page_bare, page_react, page_react_dep (renamed from _page_react.py)
  _reactive_output.py     # NEW unified decorator (replaces _render.py + _render_json.py)
  _send_message.py        # NEW (renamed from _post_message.py / _send_json.py)
  _spa_app.py             # SpaApp (HTMLDependency name + bundle filename updated)
  www/                    # Built JS bundle: shinyreact.js + shinyreact.css

pkg-py/tests/
  test_spec.py
  test_output.py
  test_page.py
  test_reactive_output.py # consolidated from test_render.py + test_render_json.py
  test_send_message.py
  test_spa_app.py

js/src/
  index.ts                # window.shinyreact, .shinyreact-output binding
  registry.ts
  renderer.tsx
  spec.ts
  shinyreact.css          # renamed from shinyjson.css
  shiny.d.ts
  shiny-react/

js/dist/shinyreact.js     # renamed from shinyjson.js

examples/
  traditional/
    01-hello-world/
    02-inputs/
    ...                   # ports of legacy examples 1-9 (page_react + reactive_output of Spec/Node)
  spa/
    01-hello/
    02-columns/
    ...                   # ports of SPA examples 13-18 (SpaApp + reactive_output of plain JSON)

docs/
  features.md             # merged (replaces features.md + features-shinyjson-old.md)
  spa-vs-traditional.md   # NEW (delivers #44)
  todos.md                # rewritten
```

---

## Task 1: Branch + worktree sanity check

**Files:** none

- [ ] **Step 1: Confirm we're on the right branch and the spec is committed**

Run:
```bash
git rev-parse --abbrev-ref HEAD
git log --oneline -1 -- docs/superpowers/specs/2026-05-05-shinyreact-merge-design.md
```

Expected: branch `schloerke/merge-old-back`; one commit shown for the spec. If either is wrong, stop and fix before continuing.

---

## Task 2: Create empty `shinyreact` package skeleton

**Files:**
- Create: `pkg-py/src/shinyreact/__init__.py`
- Create: `pkg-py/src/shinyreact/www/.gitkeep`

- [ ] **Step 1: Create the package directory with an empty `__init__.py`**

```bash
mkdir -p pkg-py/src/shinyreact/www
touch pkg-py/src/shinyreact/www/.gitkeep
```

Write `pkg-py/src/shinyreact/__init__.py`:
```python
# shinyreact: Shiny UI infrastructure for React-based component rendering.
# Public API is wired up as modules land — see docs/superpowers/plans/2026-05-05-shinyreact-merge.md.
```

- [ ] **Step 2: Commit the skeleton**

```bash
git add pkg-py/src/shinyreact/
git commit -m "feat(shinyreact): create empty package skeleton"
```

---

## Task 3: Port `_spec.py` (Spec, Node, Element)

**Files:**
- Create: `pkg-py/src/shinyreact/_spec.py`
- Reference: `pkg-py/src/shinyjsonold/_spec.py`

- [ ] **Step 1: Copy `_spec.py` byte-for-byte from `shinyjsonold`**

```bash
cp pkg-py/src/shinyjsonold/_spec.py pkg-py/src/shinyreact/_spec.py
```

- [ ] **Step 2: Sweep references in the copied file**

Open `pkg-py/src/shinyreact/_spec.py`. In docstrings and comments, replace `shinyjson`/`shinyjsonold` → `shinyreact`. Do NOT change `Spec`, `Node`, `Element` symbol names.

Verify:
```bash
grep -n "shinyjson" pkg-py/src/shinyreact/_spec.py
```
Expected: no output.

- [ ] **Step 3: Wire into `__init__.py`**

Append to `pkg-py/src/shinyreact/__init__.py`:
```python
from ._spec import Element, Node, Spec

__all__ = ["Element", "Node", "Spec"]
```

- [ ] **Step 4: Smoke-test the import**

Run: `uv run python -c "from shinyreact import Spec, Node, Element; print(Spec, Node, Element)"`

Expected: three `<class ...>` lines, no errors. (If `shinyreact` isn't yet on the install path, add `pkg-py/src/shinyreact` to the hatchling `packages` list in `pyproject.toml` first — see Task 14.)

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyreact/_spec.py pkg-py/src/shinyreact/__init__.py
git commit -m "feat(shinyreact): port Spec/Node/Element"
```

---

## Task 4: Port `_output.py` (`ui_output` + `_dep`)

**Files:**
- Create: `pkg-py/src/shinyreact/_output.py`
- Reference: `pkg-py/src/shinyjsonold/_output.py`

- [ ] **Step 1: Write `pkg-py/src/shinyreact/_output.py`**

```python
from pathlib import Path
from typing import Sequence

from htmltools import HTMLDependency, Tag, div


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyreact",
        version="0.1.0",
        source={"subdir": str(Path(__file__).parent / "www")},
        script={"src": "shinyreact.js", "defer": ""},
        stylesheet={"href": "shinyreact.css"},
    )


def ui_output(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag:
    """Create a Shiny output placeholder for a shinyreact renderer.

    Args:
        id: The output ID. Must match the server-side ``@shinyreact.reactive_output``
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

- [ ] **Step 2: Update `__init__.py`**

```python
from ._output import ui_output
from ._spec import Element, Node, Spec

__all__ = ["Element", "Node", "Spec", "ui_output"]
```

- [ ] **Step 3: Verify imports**

Run: `uv run python -c "from shinyreact import ui_output; print(ui_output('x'))"`

Expected: a `<div id="x" class="shinyreact-output">…</div>` representation.

- [ ] **Step 4: Commit**

```bash
git add pkg-py/src/shinyreact/_output.py pkg-py/src/shinyreact/__init__.py
git commit -m "feat(shinyreact): port ui_output + _dep with shinyreact naming"
```

---

## Task 5: Port `_page.py` (page_bare, page_react, page_react_dep)

**Files:**
- Create: `pkg-py/src/shinyreact/_page.py`
- Reference: `pkg-py/src/shinyjsonold/_page_react.py`

- [ ] **Step 1: Copy with rename**

```bash
cp pkg-py/src/shinyjsonold/_page_react.py pkg-py/src/shinyreact/_page.py
```

- [ ] **Step 2: Sweep references**

In `pkg-py/src/shinyreact/_page.py`, replace `shinyjson`/`shinyjsonold` → `shinyreact` in all docstrings and comments. The `from ._output import _dep` import stays as-is (relative path).

Verify:
```bash
grep -n "shinyjson" pkg-py/src/shinyreact/_page.py
```
Expected: no output.

- [ ] **Step 3: Update `__init__.py`**

```python
from ._output import ui_output
from ._page import page_bare, page_react, page_react_dep
from ._spec import Element, Node, Spec

__all__ = [
    "Element",
    "Node",
    "Spec",
    "page_bare",
    "page_react",
    "page_react_dep",
    "ui_output",
]
```

- [ ] **Step 4: Verify**

Run: `uv run python -c "from shinyreact import page_react, page_bare, page_react_dep; print('ok')"`

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyreact/_page.py pkg-py/src/shinyreact/__init__.py
git commit -m "feat(shinyreact): port page_bare/page_react/page_react_dep"
```

---

## Task 6: Write tests for unified `reactive_output` (TDD red)

**Files:**
- Create: `pkg-py/tests/test_reactive_output.py`

- [ ] **Step 1: Write the failing test file**

```python
"""Tests for the unified reactive_output decorator.

Covers all behaviors that previously lived in shinyjson.render_json (passthrough)
and shinyjsonold.render (Spec/Node flattening + auto_output_ui).
"""
from __future__ import annotations

import pytest

from shinyreact import Element, Node, Spec, reactive_output


@pytest.mark.asyncio
async def test_passthrough_dict() -> None:
    """Plain dicts pass through unchanged for useShinyOutput consumption."""
    @reactive_output
    def out():
        return {"a": 1, "b": [2, 3]}

    result = await out._fn()
    transformed = await out.transform(result)
    assert transformed == {"a": 1, "b": [2, 3]}


@pytest.mark.asyncio
async def test_passthrough_primitive() -> None:
    @reactive_output
    def out():
        return 42

    result = await out._fn()
    assert await out.transform(result) == 42


@pytest.mark.asyncio
async def test_spec_flattened() -> None:
    """Spec values are flattened via Spec.to_dict()."""
    spec = Spec(
        root="r",
        elements={"r": Element(type="Card", props={"title": "Hi"})},
    )

    @reactive_output
    def out():
        return spec

    result = await out._fn()
    assert await out.transform(result) == spec.to_dict()


@pytest.mark.asyncio
async def test_node_flattened() -> None:
    """Node values are flattened via Node.to_spec().to_dict()."""
    node = Node(type="Card", props={"title": "Hi"})

    @reactive_output
    def out():
        return node

    result = await out._fn()
    assert await out.transform(result) == node.to_spec().to_dict()


def test_auto_output_ui_returns_ui_output() -> None:
    """Express mode auto-generates a shinyreact-output container."""
    @reactive_output
    def my_card():
        return {"x": 1}

    tag = my_card.auto_output_ui()
    rendered = str(tag)
    assert "shinyreact-output" in rendered
    assert 'id="my_card"' in rendered


def test_no_extra_deps_attribute() -> None:
    """The unified decorator drops the extra_deps extension hook."""
    assert not hasattr(reactive_output, "extra_deps")
```

- [ ] **Step 2: Run the test, verify it fails**

Run: `uv run pytest pkg-py/tests/test_reactive_output.py -v`

Expected: ImportError or AttributeError on `reactive_output` — the symbol doesn't exist yet.

- [ ] **Step 3: Commit the failing test**

```bash
git add pkg-py/tests/test_reactive_output.py
git commit -m "test(shinyreact): add failing tests for unified reactive_output"
```

---

## Task 7: Implement `reactive_output` (TDD green)

**Files:**
- Create: `pkg-py/src/shinyreact/_reactive_output.py`
- Modify: `pkg-py/src/shinyreact/__init__.py`

- [ ] **Step 1: Write `_reactive_output.py`**

```python
from htmltools import Tag
from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._output import ui_output
from ._spec import Node, Spec


class reactive_output(Renderer[Spec | Node | Jsonifiable]):
    """Reactive output decorator for shinyreact.

    The server-side counterpart to ``useShinyOutput()`` on the React client.
    Accepts:

    * :class:`~shinyreact.Spec` — pre-flattened component tree, serialized via
      :meth:`Spec.to_dict`.
    * :class:`~shinyreact.Node` — nested component tree, flattened via
      :meth:`Node.to_spec` first.
    * Any JSON-serializable value (``dict``, ``list``, ``str``, ``int``,
      ``float``, ``None``) — passed through unchanged.

    In Shiny Express mode the decorator auto-generates a
    :func:`~shinyreact.ui_output` container at the corresponding output ID.

    Downstream packages that need to inject extra HTMLDependencies attach
    them on the UI side via ``shinyreact.ui_output(id, extra_deps=[...])``.

    Example -- plain JSON for ``useShinyOutput()``::

        @shinyreact.reactive_output
        def my_data():
            return {"key": "value", "count": 42}

    Example -- Spec-based rendering::

        @shinyreact.reactive_output
        def my_card() -> shinyreact.Spec:
            return shinyreact.Spec(
                root="card",
                elements={
                    "card": shinyreact.Element(
                        type="Card", props={"title": "Hi"}
                    ),
                },
            )
    """

    async def transform(self, value: Spec | Node | Jsonifiable) -> Jsonifiable:
        if isinstance(value, Node):
            return value.to_spec().to_dict()
        if isinstance(value, Spec):
            return value.to_dict()
        return value

    def auto_output_ui(self) -> Tag:
        return ui_output(self.output_id)
```

- [ ] **Step 2: Wire into `__init__.py`**

```python
from ._output import ui_output
from ._page import page_bare, page_react, page_react_dep
from ._reactive_output import reactive_output
from ._spec import Element, Node, Spec

__all__ = [
    "Element",
    "Node",
    "Spec",
    "page_bare",
    "page_react",
    "page_react_dep",
    "reactive_output",
    "ui_output",
]
```

- [ ] **Step 3: Run the tests**

Run: `uv run pytest pkg-py/tests/test_reactive_output.py -v`

Expected: all 6 tests pass. If `_fn` access fails (Renderer internals may differ across Shiny versions), adjust the test to call the wrapped function however the existing `pkg-py/tests/old/test_render.py` does.

- [ ] **Step 4: Commit**

```bash
git add pkg-py/src/shinyreact/_reactive_output.py pkg-py/src/shinyreact/__init__.py
git commit -m "feat(shinyreact): unified reactive_output decorator"
```

---

## Task 8: Port `send_message`

**Files:**
- Create: `pkg-py/src/shinyreact/_send_message.py`
- Create: `pkg-py/tests/test_send_message.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for shinyreact.send_message (renamed from post_message / send_json)."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from shinyreact import send_message


@pytest.mark.asyncio
async def test_send_message_wraps_in_shiny_react_message() -> None:
    session = AsyncMock()
    session.ns = ""

    # resolve_id uses session via shiny.module — patch only what we need.
    from shiny.module import resolve_id  # noqa: F401

    await send_message(session, "notification", {"text": "hi"})

    session.send_custom_message.assert_awaited_once()
    call = session.send_custom_message.await_args
    assert call.args[0] == "shinyReactMessage"
    payload = call.args[1]
    assert payload["type"].endswith("notification")
    assert payload["data"] == {"text": "hi"}
```

Run: `uv run pytest pkg-py/tests/test_send_message.py -v`

Expected: ImportError — `send_message` doesn't exist yet.

- [ ] **Step 2: Write `_send_message.py`**

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shiny.module import resolve_id

if TYPE_CHECKING:
    from shiny.session import Session
    from shiny.types import Jsonifiable


async def send_message(
    session: Session,
    type: str,
    data: Jsonifiable,
) -> None:
    """Send a custom message from server to client React components.

    Messages are consumed by ``useShinyMessageHandler(type, handler)`` on the
    React side via the ``@posit/shiny-react`` hooks bundled in shinyreact.

    Args:
        session: The Shiny session to send the message through.
        type: The message type string. Must match the ``messageType`` argument
            passed to ``useShinyMessageHandler()`` in the React component.
        data: Any JSON-serializable data to include in the message.

    Example::

        @reactive.effect
        async def notify():
            await shinyreact.send_message(
                session, "notification", {"text": "Hello!", "level": "info"}
            )
    """
    namespaced_type = resolve_id(type)
    await session.send_custom_message(
        "shinyReactMessage", {"type": namespaced_type, "data": data}
    )
```

- [ ] **Step 3: Wire into `__init__.py`**

```python
from ._output import ui_output
from ._page import page_bare, page_react, page_react_dep
from ._reactive_output import reactive_output
from ._send_message import send_message
from ._spec import Element, Node, Spec

__all__ = [
    "Element",
    "Node",
    "Spec",
    "page_bare",
    "page_react",
    "page_react_dep",
    "reactive_output",
    "send_message",
    "ui_output",
]
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest pkg-py/tests/test_send_message.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyreact/_send_message.py pkg-py/src/shinyreact/__init__.py pkg-py/tests/test_send_message.py
git commit -m "feat(shinyreact): send_message (replaces post_message and send_json)"
```

---

## Task 9: Port `SpaApp` with new naming

**Files:**
- Create: `pkg-py/src/shinyreact/_spa_app.py`
- Reference: `pkg-py/src/shinyjson/_spa_app.py`

- [ ] **Step 1: Write `_spa_app.py`**

```python
from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable

from htmltools import HTML, HTMLDependency, TagList
from shiny import App
from shiny.session import Inputs, Outputs, Session


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyreact",
        version="0.1.0",
        source={"subdir": str(Path(__file__).parent / "www")},
        script={"src": "shinyreact.js", "defer": ""},
        stylesheet={"href": "shinyreact.css"},
    )


class SpaApp(App):
    """A Shiny app that serves a static SPA from a directory of assets.

    The directory must contain an ``index.html`` file. All files in it are
    served as static assets. The server function contains only reactive
    computation and business logic — no UI definitions.

    Args:
        server: The Shiny server function.
        static_dir: Path to the directory containing ``index.html`` and static
            assets. Defaults to ``./www`` relative to the file that constructs
            ``SpaApp`` (typically the app's ``app.py``).

    Example::

        from shinyreact import SpaApp

        def server(input, output, session):
            ...

        app = SpaApp(server)  # serves ./www/ next to this file
    """

    def __init__(
        self,
        server: Callable[[Inputs, Outputs, Session], None],
        *,
        static_dir: str | Path | None = None,
        **kwargs: Any,
    ) -> None:
        if static_dir is None:
            caller_file = inspect.stack()[1].filename
            static_dir = Path(caller_file).parent / "www"
        static_dir = Path(static_dir)
        ui = TagList(
            _dep(),
            HTML((static_dir / "index.html").read_text()),
        )
        super().__init__(ui, server, static_assets=static_dir, **kwargs)
```

Note the two changes from the original `shinyjson/_spa_app.py`: HTMLDependency `name="shinyreact"` and `script={"src": "shinyreact.js", ...}`, plus the docstring says `from shinyreact import SpaApp`.

- [ ] **Step 2: Wire into `__init__.py` (final form)**

```python
from ._output import ui_output
from ._page import page_bare, page_react, page_react_dep
from ._reactive_output import reactive_output
from ._send_message import send_message
from ._spa_app import SpaApp
from ._spec import Element, Node, Spec

__all__ = [
    "Element",
    "Node",
    "Spec",
    "SpaApp",
    "page_bare",
    "page_react",
    "page_react_dep",
    "reactive_output",
    "send_message",
    "ui_output",
]
```

- [ ] **Step 3: Verify import**

Run: `uv run python -c "from shinyreact import SpaApp; print(SpaApp)"`

Expected: a class repr.

- [ ] **Step 4: Commit**

```bash
git add pkg-py/src/shinyreact/_spa_app.py pkg-py/src/shinyreact/__init__.py
git commit -m "feat(shinyreact): SpaApp with shinyreact HTMLDependency naming"
```

---

## Task 10: Port `test_spec.py` and `test_output.py`

**Files:**
- Create: `pkg-py/tests/test_spec.py`
- Create: `pkg-py/tests/test_output.py`
- Reference: `pkg-py/tests/old/test_spec.py`, `pkg-py/tests/old/test_output.py`

- [ ] **Step 1: Copy + sweep `test_spec.py`**

```bash
cp pkg-py/tests/old/test_spec.py pkg-py/tests/test_spec.py
```

Open the new file. Replace every `from shinyjsonold` / `import shinyjsonold` with `from shinyreact` / `import shinyreact`. Replace any `shinyjson`/`shinyjsonold` in docstrings or assertion messages with `shinyreact`. The `Spec`/`Node`/`Element` API is unchanged so test bodies should otherwise stand.

Verify: `grep -n "shinyjson" pkg-py/tests/test_spec.py` → no output.

Run: `uv run pytest pkg-py/tests/test_spec.py -v` → PASS.

- [ ] **Step 2: Copy + sweep `test_output.py`**

```bash
cp pkg-py/tests/old/test_output.py pkg-py/tests/test_output.py
```

Same sweep. The container CSS class changed from `shinyjson-output` to `shinyreact-output` — update assertions accordingly. The HTMLDependency name changed too (`shinyjsonold` → `shinyreact`); update any direct assertions.

Run: `uv run pytest pkg-py/tests/test_output.py -v` → PASS.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/tests/test_spec.py pkg-py/tests/test_output.py
git commit -m "test(shinyreact): port spec and output tests"
```

---

## Task 11: Port `test_page.py` and `test_spa_app.py`

**Files:**
- Create: `pkg-py/tests/test_page.py`
- Modify-in-place: `pkg-py/tests/test_spa_app.py` (already exists in new tests/, currently imports `shinyjson`)

- [ ] **Step 1: Port `test_page.py`**

```bash
cp pkg-py/tests/old/test_page.py pkg-py/tests/test_page.py
```

Sweep `shinyjsonold` → `shinyreact` and `shinyjson` (the JS/CSS asset name) → `shinyreact` (file references like `shinyjson.js` → `shinyreact.js`, `shinyjson.css` → `shinyreact.css`).

Run: `uv run pytest pkg-py/tests/test_page.py -v` → PASS.

- [ ] **Step 2: Update existing `test_spa_app.py`**

Open `pkg-py/tests/test_spa_app.py`. Replace `from shinyjson` → `from shinyreact`. Update any expected asset filename strings (`shinyjson.js` → `shinyreact.js`, `shinyjson.css` → `shinyreact.css`) and HTMLDependency name strings (`"shinyjson"` → `"shinyreact"`).

Run: `uv run pytest pkg-py/tests/test_spa_app.py -v` → PASS.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/tests/test_page.py pkg-py/tests/test_spa_app.py
git commit -m "test(shinyreact): port page and spa_app tests"
```

---

## Task 12: Delete the old test directory and obsolete tests

**Files:**
- Delete: `pkg-py/tests/old/`
- Delete: `pkg-py/tests/test_render_json.py`
- Delete: `pkg-py/tests/test_send_json.py`

- [ ] **Step 1: Confirm parity**

Run: `uv run pytest pkg-py/tests/ -v --ignore=pkg-py/tests/old`

Expected: every behavior in `tests/old/test_render.py` and `tests/old/test_post_message.py` is now covered by `test_reactive_output.py` and `test_send_message.py`. If anything is missing, port it before deleting.

- [ ] **Step 2: Delete**

```bash
git rm -r pkg-py/tests/old
git rm pkg-py/tests/test_render_json.py pkg-py/tests/test_send_json.py
```

- [ ] **Step 3: Run the full Python test suite**

Run: `uv run pytest pkg-py/tests/ -v`

Expected: all pass, no references to old packages.

- [ ] **Step 4: Commit**

```bash
git commit -m "test: remove shinyjson and shinyjsonold test files"
```

---

## Task 13: JS-side renames

**Files:**
- Rename: `js/src/shinyjson.css` → `js/src/shinyreact.css`
- Modify: `js/src/index.ts`
- Modify: `js/src/registry.ts`, `js/src/renderer.tsx` (if they reference `shinyjson`)
- Modify: `js/package.json` (if bundle output filename is configured there or in `vite.config.ts`)
- Modify: `js/vite.config.ts` if applicable
- Modify: `js/src/__tests__/*` if they reference the global

- [ ] **Step 1: Rename the CSS file**

```bash
git mv js/src/shinyjson.css js/src/shinyreact.css
```

- [ ] **Step 2: Sweep JS sources**

In `js/src/index.ts`, change:
- `import "./shinyjson.css"` → `import "./shinyreact.css"`
- `window.shinyjson` (declaration block + assignment) → `window.shinyreact`
- The interface in `declare global { interface Window { shinyjson: {...} } }` → `shinyreact: {...}`
- `class ShinyjsonOutputBinding` → `class ShinyreactOutputBinding` (and the `Shiny.outputBindings.register(new ..., "shinyjson.binding")` ID → `"shinyreact.binding"`)
- The CSS class selector `".shinyjson-output"` → `".shinyreact-output"`

In `js/src/registry.ts`, `js/src/renderer.tsx`: search for `shinyjson` (case-insensitive) and rename to `shinyreact` everywhere except where it's a comment about historical context (no such cases exist — sweep all of them).

In `js/src/__tests__/`: same sweep.

Verify:
```bash
grep -rni "shinyjson" js/src/
```
Expected: no output.

- [ ] **Step 3: Update Vite output filename**

Open `js/vite.config.ts` (or `vite.config.js`). Find the `build.lib.fileName` or `rollupOptions.output.entryFileNames` and change `shinyjson` → `shinyreact`. Also check `package.json` `"name"` field (if it's `shinyjson`, rename to `shinyreact`; verify with the user before changing if uncertain — the npm name may be unrelated to the IIFE bundle filename).

- [ ] **Step 4: Build the JS bundle**

Run: `make js-build`

Expected: `js/dist/shinyreact.js` and `js/dist/shinyreact.css` produced; no `js/dist/shinyjson.*` files.

If `js/dist/shinyjson.js` still exists from a prior build, delete it: `git rm js/dist/shinyjson.js js/dist/shinyjson.css 2>/dev/null || true`.

- [ ] **Step 5: Run JS lint and tests**

```bash
make js-lint
cd js && npx vitest run
cd ..
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add js/ -A
git commit -m "refactor(js): rename shinyjson → shinyreact (window global, CSS class, bundle)"
```

---

## Task 14: Update `pyproject.toml` and `Makefile`

**Files:**
- Modify: `pyproject.toml`
- Modify: `Makefile`

- [ ] **Step 1: Update `pyproject.toml`**

In `pyproject.toml`:

```toml
[project]
name = "shinyreact"
# ... (rest unchanged)

[tool.hatch.build.targets.wheel]
packages = ["pkg-py/src/shinyreact"]

[tool.pyright]
include = ["pkg-py/src/shinyreact"]
# ... (rest unchanged)
```

Confirm there are no other `shinyjson`/`shinyjsonold` references.

- [ ] **Step 2: Update `Makefile`**

Find every occurrence of `shinyjson` or `shinyjsonold` in `Makefile`. Update:
- The `update-dist` target: `cp js/dist/shinyjson.js pkg-py/src/shinyjson/www/...` → `cp js/dist/shinyreact.js pkg-py/src/shinyreact/www/...` (and the `.css` line). Update the `pkg-r/inst/lib/shiny/` copy line similarly (filename `shinyjson.js`→`shinyreact.js`).
- Any test/check targets pointing into `pkg-py/src/shinyjson` or `pkg-py/src/shinyjsonold`.

Verify: `grep -n "shinyjson" Makefile` → no output.

- [ ] **Step 3: Re-sync env and run full check**

```bash
uv sync --all-extras --all-groups
make update-dist
make py-check
```

Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml Makefile
git commit -m "build: rename package shinyjson → shinyreact in pyproject and Makefile"
```

---

## Task 15: Delete the old `shinyjson` and `shinyjsonold` packages

**Files:**
- Delete: `pkg-py/src/shinyjson/`
- Delete: `pkg-py/src/shinyjsonold/`

- [ ] **Step 1: Delete both packages**

```bash
git rm -r pkg-py/src/shinyjson pkg-py/src/shinyjsonold
```

- [ ] **Step 2: Sanity-check there are no Python references left**

Run:
```bash
grep -rni "shinyjson" pkg-py/src/ Makefile pyproject.toml
```

Expected: no output. If anything matches, fix before continuing.

- [ ] **Step 3: Run the full Python check**

Run: `make py-check`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: delete shinyjson and shinyjsonold packages"
```

---

## Task 16: Reorganize examples — directory layout

**Files:**
- Create: `examples/traditional/` and `examples/spa/`
- Move and rename existing example directories.

- [ ] **Step 1: Decide which example goes in which subdir**

Open each existing example's `app.py`. If it imports from `shinyjsonold` and uses `page_react` + the old `render` decorator returning `Spec`/`Node`, it's **traditional**. If it imports from `shinyjson` and uses `SpaApp` + `render_json`, it's **spa**.

Mapping (verify per example):
- `examples/1-hello-world/` → `examples/traditional/01-hello-world/`
- `examples/2-inputs/` → `examples/traditional/02-inputs/`
- `examples/3-outputs/` → `examples/traditional/03-outputs/`
- `examples/4-messages/` → `examples/traditional/04-messages/`
- `examples/5-shadcn/` → `examples/traditional/05-shadcn/`
- `examples/6-dashboard/` → `examples/traditional/06-dashboard/`
- `examples/7-chat/` → `examples/traditional/07-chat/`
- `examples/8-modules/` → `examples/traditional/08-modules/`
- `examples/9-blended/` → `examples/traditional/09-blended/`
- `examples/11-columns-traditional/` → `examples/traditional/10-columns/`
- `examples/10-spa-hello/` → `examples/spa/01-hello-rough/` *(or drop if redundant with 13)*
- `examples/12-columns-spa/` → `examples/spa/02-columns-rough/` *(same caveat)*
- `examples/13-spa-hello/` → `examples/spa/01-hello/`
- `examples/14-columns-new-spa/` → `examples/spa/02-columns/`
- `examples/15-columns-shadcn/` → `examples/spa/03-columns-shadcn/`
- `examples/16-shadcn/` → `examples/spa/04-shadcn/`
- `examples/17-hello-spa-old/` → drop or fold into spa/01-hello/ *(verify content first)*
- `examples/18-temperature/` → `examples/spa/05-temperature/`
- `examples/hello-shinyjson/` → drop *(verify it's a duplicate of an above example)*

For any example marked "drop or fold" or "rough", inspect it first and decide. Don't delete unique content.

- [ ] **Step 2: Execute the moves**

For each mapping above:
```bash
git mv examples/<old>/ examples/<bucket>/<new>/
```

Do the moves one-by-one, committing in batches of ~5 to keep diffs reviewable.

- [ ] **Step 3: Commit moves**

```bash
git commit -m "examples: reorganize into traditional/ and spa/ subdirs"
```

---

## Task 17: Sweep example imports and HTML

**Files:**
- All `examples/**/*.py`, `examples/**/*.html`, `examples/**/*.js`, `examples/**/*.tsx`, `examples/**/*.css`

- [ ] **Step 1: Sweep all example sources**

For each file under `examples/`:
- Python: `from shinyjsonold` / `import shinyjsonold` → `from shinyreact` / `import shinyreact`. `from shinyjson` / `import shinyjson` → `from shinyreact` / `import shinyreact`. Decorator/function renames: `@shinyjsonold.render` → `@shinyreact.reactive_output`, `@shinyjson.render_json` → `@shinyreact.reactive_output`, `shinyjsonold.post_message` → `shinyreact.send_message`, `shinyjson.send_json` → `shinyreact.send_message`.
- HTML/JS/TSX: `window.shinyjson` → `window.shinyreact`; `shinyjson.js` / `shinyjson.css` (asset hrefs/srcs) → `shinyreact.js` / `shinyreact.css`; class `shinyjson-output` → `shinyreact-output`.

Verify:
```bash
grep -rni "shinyjson" examples/
```
Expected: no output.

- [ ] **Step 2: Smoke-test one example per pattern**

Pick `examples/traditional/01-hello-world/` and `examples/spa/01-hello/`. For each:
```bash
uv run shiny run --port 0 examples/<path>/app.py &
sleep 2
# curl localhost:<port> and grep for "shinyreact-output" or window.shinyreact
kill %1
```

Expected: Shiny starts cleanly; rendered HTML mentions `shinyreact`, not `shinyjson`.

- [ ] **Step 3: Commit**

```bash
git add examples/
git commit -m "examples: rename shinyjson/shinyjsonold imports → shinyreact"
```

---

## Task 18: Merge feature docs

**Files:**
- Modify: `docs/features.md` (becomes the merged file)
- Delete: `docs/features-shinyjson-old.md`

- [ ] **Step 1: Merge content**

Open both `docs/features.md` (current SPA-first inventory) and `docs/features-shinyjson-old.md` (legacy inventory). Produce a single `docs/features.md` organized in two top-level sections: "Traditional pattern (`page_react` + `reactive_output`)" and "SPA pattern (`SpaApp`)". Each section lists the relevant features with the new public-API names. No `shinyjson`/`shinyjsonold` mentions.

- [ ] **Step 2: Delete the legacy file**

```bash
git rm docs/features-shinyjson-old.md
```

- [ ] **Step 3: Verify**

```bash
grep -n "shinyjson" docs/features.md
```
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add docs/features.md
git commit -m "docs: merge features-shinyjson-old.md into features.md"
```

---

## Task 19: Write `docs/spa-vs-traditional.md` (delivers #44)

**Files:**
- Create: `docs/spa-vs-traditional.md`
- Modify: `README.md` (link the new doc)
- Modify: `docs/features.md` (link the new doc)

- [ ] **Step 1: Write `docs/spa-vs-traditional.md`**

Use issue #44's seven-section outline:

1. **Framing — what's actually different.** Both patterns are valid Shiny apps. Difference is *where UI logic lives* and *what travels over the websocket*: traditional ships HTML/JS, shinyreact's SPA mode ships JSON. Note `server + index.html` already exists in core Shiny.
2. **Side-by-side file layout.** Traditional `app.py` with `page_react()` + `reactive_output` of `Spec`/`Node`. SPA: `app.py` (server only) + `www/index.html` + `www/index.tsx` (or plain JS). Link to `examples/traditional/10-columns/` vs `examples/spa/02-columns/`, and `examples/traditional/01-hello-world/` vs `examples/spa/01-hello/`.
3. **What goes over the websocket.** Traditional: HTML/JS down. SPA: JSON down via `reactive_output`, consumed by `useShinyOutput()`.
4. **Dev workflow.** Traditional: edit `app.py`, reload. SPA: hand-written JS *or* JSX + Vite.
5. **Tradeoffs.** Strengths/weaknesses of each — copy from issue #44.
6. **"Pick this if…" guidance.** Per-pattern recommendations.
7. **Migration note.** Patterns coexist in `shinyreact`; a `SpaApp` can be one piece of a larger system.

Every example reference must be a clickable relative path into `examples/traditional/...` or `examples/spa/...`.

- [ ] **Step 2: Add links from README and features.md**

Add a line under the project intro in `README.md`:
> See [docs/spa-vs-traditional.md](docs/spa-vs-traditional.md) for the difference between the traditional and SPA patterns.

Add a top-of-page link in `docs/features.md`.

- [ ] **Step 3: Commit**

```bash
git add docs/spa-vs-traditional.md README.md docs/features.md
git commit -m "docs: add spa-vs-traditional.md (closes #44 when merged)"
```

---

## Task 20: Sweep remaining docs and decisions

**Files:**
- `CLAUDE.md`, `DESIGN.md`, `docs/todos.md`, `docs/TIMELINE.md`, `decisions/*`

- [ ] **Step 1: List remaining hits**

Run:
```bash
grep -rln "shinyjson" CLAUDE.md DESIGN.md docs/ decisions/
```

This produces the file list. Open each and rewrite:
- Package references: `shinyjson` / `shinyjsonold` → `shinyreact`.
- API references: `render_json`, `render` (in shinyreact context) → `reactive_output`. `post_message`, `send_json` → `send_message`.
- DESIGN.md §1 / §8 / §9 (or wherever it discusses SPA-first as a prototype): rewrite to "shinyreact ships both patterns; SPA-first and traditional are first-class peers."
- `docs/todos.md`: drop entries about retiring `shinyjsonold` or about the SPA-first/legacy split. Add (if not present): the items implicit in this plan that aren't yet fully landed (e.g., R package).

The `docs/superpowers/specs/` and `docs/superpowers/plans/` files are *historical* — leave their existing content alone (they describe the old state at the time they were written). The spec for *this* work and this plan itself are the exception (they describe the new state).

- [ ] **Step 2: Verify**

```bash
grep -rln "shinyjson" CLAUDE.md DESIGN.md docs/todos.md docs/TIMELINE.md decisions/
```

Expected: no output. (Files under `docs/superpowers/specs/` and `docs/superpowers/plans/` other than today's two files may still mention `shinyjson` historically — that's fine.)

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md DESIGN.md docs/todos.md docs/TIMELINE.md decisions/
git commit -m "docs: rewrite shinyjson/shinyjsonold references to shinyreact"
```

---

## Task 21: Update CLAUDE.md repo-structure block

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Replace the repo-structure section**

The "Repo structure" block in CLAUDE.md currently shows two Python packages and `pkg-py/tests/old/`. Replace with the new layout (single `pkg-py/src/shinyreact/`, single `pkg-py/tests/`, `examples/traditional/`, `examples/spa/`). Update the "Architecture" section's references to module paths. Update the "Downstream package pattern" code block to use `class render(shinyreact.reactive_output):` and `from shinyreact import ui_output`.

- [ ] **Step 2: Verify**

`grep -n "shinyjson" CLAUDE.md` → no output.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md repo structure for shinyreact"
```

---

## Task 22: Repo-wide final sweep

**Files:** all tracked files.

- [ ] **Step 1: Hunt for any leftover `shinyjson` references**

Run:
```bash
grep -rln "shinyjson" \
  --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv \
  --exclude-dir=docs/superpowers/specs --exclude-dir=docs/superpowers/plans \
  .
```

Allowed remaining matches: only `docs/superpowers/specs/` and `docs/superpowers/plans/` files that document past states (and the one for *this* work, which intentionally references the rename).

If anything else matches, fix it.

- [ ] **Step 2: Run all checks**

```bash
make js-build
make update-dist
make py-check
make js-lint
cd js && npx vitest run; cd ..
```

Expected: all green.

- [ ] **Step 3: Commit (only if Step 1 found anything)**

```bash
git add -A
git commit -m "refactor: final shinyjson → shinyreact sweep"
```

---

## Task 23: Update GitHub issues

**Files:** none in the repo — these are GitHub edits.

For each issue, edit the body via `gh issue edit <num> --body-file -` (or open in browser). Keep titles unless explicitly noted.

- [ ] **Step 1: Issue #38 (rename)**

Restate: rename happens; the traditional pattern is **kept**, not retired. Trim retirement-related sections. Title can become "Rename shinyjson → shinyreact" (drop "at the same release that retires shinyjsonold").

- [ ] **Step 2: Issue #37 (closed: retire shinyjsonold)**

Post a comment that the retirement track is reversed — the traditional pattern is folded back into `shinyreact`. Link to `docs/superpowers/specs/2026-05-05-shinyreact-merge-design.md`. Leave the issue closed.

```bash
gh issue comment 37 --body "Reversed: traditional JSON-spec pattern folded back into a renamed \`shinyreact\` package alongside the SPA-first API. See docs/superpowers/specs/2026-05-05-shinyreact-merge-design.md."
```

- [ ] **Step 3: Issue #51 (rename render_json → reactive_output)**

Mark superseded. Update body to note that `reactive_output` is now the **unified** decorator (accepts `Spec | Node | Jsonifiable`, drops `extra_deps`), not just a rename. Link the spec. Close the issue if the merge work delivers it.

- [ ] **Step 4: Issue #44 (spa-vs-traditional docs)**

Update naming references (`shinyjson` → `shinyreact`). Note this work delivers the doc directly. Close on merge.

- [ ] **Step 5: Issues #33, #34**

Update bodies: `shinyjson` → `shinyreact`. For #34 (Claude scaffolding skill), note that templates must offer **both** patterns (traditional and SPA) and use unified API names (`reactive_output`, `send_message`).

- [ ] **Step 6: Issues #27, #28, #30, #31, #32, #35, #36, #39, #49, #50**

Pure rename pass: `shinyjson` / `shinyjsonold` → `shinyreact`, `render_json`/`render` → `reactive_output`, `post_message`/`send_json` → `send_message`. Keep all other semantics. Use `gh issue view <num> --json body` to fetch, edit locally, push back with `gh issue edit <num> --body-file -`.

- [ ] **Step 7: Verify**

```bash
for n in 27 28 30 31 32 33 34 35 36 38 39 44 49 50 51; do
  gh issue view $n --json body --jq .body | grep -i "shinyjson" && echo ">>> issue $n still has shinyjson"
done
```

Expected: no `>>> issue ...` lines.

---

## Task 24: Open the PR

**Files:** none.

- [ ] **Step 1: Push the branch**

```bash
git push -u origin schloerke/merge-old-back
```

- [ ] **Step 2: Open the PR**

```bash
gh pr create --base main --title "Merge shinyjsonold back into renamed shinyreact" --body "$(cat <<'EOF'
## Summary

- Replaces `shinyjson` (SPA-first) and `shinyjsonold` (JSON-spec) with one package, `shinyreact`, that ships both patterns intentionally.
- Unifies `render_json` + `render` → `reactive_output(Spec | Node | Jsonifiable)`. Drops `extra_deps`; downstream packages inject deps via `ui_output`.
- Unifies `post_message` + `send_json` → `send_message` (pairs cleanly with JS `useShinyMessageHandler`).
- Renames JS globals: `window.shinyjson` → `window.shinyreact`; `class="shinyjson-output"` → `class="shinyreact-output"`; HTMLDependency name and bundle filename to `shinyreact`.
- Reorganizes `examples/` into `examples/traditional/` and `examples/spa/`.
- Adds `docs/spa-vs-traditional.md` (closes #44).
- Updates open issues to reflect the new package layout.

Spec: `docs/superpowers/specs/2026-05-05-shinyreact-merge-design.md`
Plan: `docs/superpowers/plans/2026-05-05-shinyreact-merge.md`

Closes #38, #44, #51.
Reverses #37 (commented).

## Test plan

- [ ] `make py-check` passes
- [ ] `make js-lint` and `cd js && npx vitest run` pass
- [ ] `make js-build && make update-dist` produces `pkg-py/src/shinyreact/www/shinyreact.{js,css}`
- [ ] `grep -rn shinyjson . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=docs/superpowers/specs --exclude-dir=docs/superpowers/plans` is empty
- [ ] One traditional example boots (`examples/traditional/01-hello-world/`)
- [ ] One SPA example boots (`examples/spa/01-hello/`)
EOF
)"
```

- [ ] **Step 3: Verify CI**

Watch the PR's checks. Fix any failures inline.

---

## Done definition

- All 24 tasks complete.
- `pkg-py/src/shinyreact/` is the only Python package.
- `make py-check`, `make js-build`, `make js-lint`, JS vitest all pass.
- No `shinyjson`/`shinyjsonold` references in code, examples, docs, Makefile, pyproject.toml, CLAUDE.md, DESIGN.md, decisions/, or open GitHub issues (excluding historical specs/plans under `docs/superpowers/`).
- PR open against `main`.
