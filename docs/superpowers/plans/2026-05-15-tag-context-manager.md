# Tag-as-Context-Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Stage A of issue #70 — make `shinyui` `AllowsChildren` components and a new `CtxTag` work as context managers, so `with card(): h1("x")` produces the same tree as positional composition. Implementation lives entirely in `pkg-py/src/shinyui/`; spec at `docs/superpowers/specs/2026-05-15-tag-context-manager-design.md`.

**Architecture:** One lazily-installed `sys.displayhook` shim that reads a per-task `contextvars.ContextVar` parent stack. `AllowsChildren.__enter__` pushes self; `__exit__` pops via a `Token`. Bare-expression values in REPL / Jupyter / Quarto / Express AST-rewritten code reach the shim and route to the stack tip via `htmltools.wrap_displayhook_handler`. Plain Python script bodies don't fire `sys.displayhook`, so the existing positional API is the fallback there.

**Tech Stack:** Python 3.10–3.14, htmltools (`Tag`, `wrap_displayhook_handler`), shiny (`expressify` for AST tests), pytest, contextvars.

---

## File Structure

**Create:**
- `pkg-py/src/shinyui/_ctx_stack.py` — module-private contextvar + lazy displayhook installer; exports `push`, `pop`.
- `pkg-py/src/shinyui/_ctx_tag.py` — `CtxTag(Tag)` subclass with contextvar-aware `__enter__` / `__exit__`.
- `pkg-py/tests/shinyui/test_ctx_stack.py` — unit tests for the stack module, `AllowsChildren` wiring, `CtxTag` wiring, async isolation, and the Express-style snapshot.
- `examples/app-py/15-shinyui-with-blocks/app.py` — Shiny Express demo using `with card(): with accordion(): ...` for the same tree shown in `14-unified-ui-prototype/`.

**Modify:**
- `pkg-py/src/shinyui/_children.py` — replace the no-op `__enter__` / `__exit__` with real bodies that call `push` / `pop`.
- `pkg-py/src/shinyui/__init__.py` — export `CtxTag`.
- `pkg-py/tests/shinyui/test_allows_children.py` — flip `test_bare_tag_in_with_block_is_not_auto_collected` to the new behavior (it now IS collected via displayhook).
- `pkg-py/tests/shinyui/test_public_exports.py` — add `CtxTag` to the export assertions.

Files that change together: `_ctx_stack.py` (mechanism) + `_children.py` (consumer) + `test_ctx_stack.py` (validation). `CtxTag` is a thin separate file because it's a public class with its own export.

---

## Task 1: `_ctx_stack` module — the contextvar + displayhook shim

**Files:**
- Create: `pkg-py/src/shinyui/_ctx_stack.py`
- Test:   `pkg-py/tests/shinyui/test_ctx_stack.py`

- [ ] **Step 1: Write the failing test**

Create `pkg-py/tests/shinyui/test_ctx_stack.py`:

```python
"""Tests for shinyui's parent-tag context stack (issue #70, Stage A).

The stack is exercised in two ways:
  - Direct ``sys.displayhook(value)`` calls — simulates what REPL / Jupyter /
    Quarto / Express's ``expressify`` AST rewriter do automatically. Lets us
    validate routing without depending on Python doing it for us.
  - One end-to-end ``@expressify`` test — confirms the AST-rewriter path that
    a real Shiny Express app uses also routes correctly.
"""

from __future__ import annotations

import asyncio
import sys

import pytest
import shinyui as sui
from htmltools import tags
from shiny.express import expressify


def test_push_pop_isolated_stack() -> None:
    """push/pop maintain a stack via Token-based reset."""
    from shinyui._ctx_stack import _stack, pop, push

    assert _stack.get() == ()
    parent_a = sui.card(id="a")
    token_a = push(parent_a)
    assert _stack.get() == (parent_a,)
    parent_b = sui.card(id="b")
    token_b = push(parent_b)
    assert _stack.get() == (parent_a, parent_b)
    pop(token_b)
    assert _stack.get() == (parent_a,)
    pop(token_a)
    assert _stack.get() == ()


def test_displayhook_appends_to_stack_tip() -> None:
    """sys.displayhook(value) inside a with-block routes to stack tip."""
    with sui.card(id="m") as c:
        sys.displayhook(tags.p("hi"))
    assert len(c.children) == 1


def test_displayhook_fall_through_outside_with_block() -> None:
    """sys.displayhook(value) outside a with-block delegates to the original
    displayhook installed before ours."""
    # Force install
    from shinyui._ctx_stack import _ensure_installed

    _ensure_installed()

    seen: list[object] = []
    saved = sys.displayhook
    try:
        # Wedge a sentinel previous-displayhook in: we save the current shim
        # (already _dispatch) and install one that records, then trigger a
        # fall-through by being outside any with-block.
        import shinyui._ctx_stack as cs

        original_prev = cs._prev_displayhook
        cs._prev_displayhook = seen.append
        try:
            sys.displayhook("untargeted")
        finally:
            cs._prev_displayhook = original_prev
    finally:
        sys.displayhook = saved

    assert seen == ["untargeted"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyui/test_ctx_stack.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'shinyui._ctx_stack'`

- [ ] **Step 3: Write minimal implementation**

Create `pkg-py/src/shinyui/_ctx_stack.py`:

```python
"""Parent-tag context stack — backs shinyui's ``with``-block child collection.

The mechanism:

1. A module-level ``contextvars.ContextVar`` holds an immutable tuple stack of
   "active parents." Per-task isolation comes from ``ContextVar`` semantics —
   each ``asyncio.Task`` gets its own copy on creation.
2. The first time any parent is entered, we lazily install a process-wide
   ``sys.displayhook`` shim. The shim reads the current task's stack:
   - non-empty → append the displayed value to the stack tip via
     ``htmltools.wrap_displayhook_handler`` (which knows how to coerce
     strings, Tags, TagLists, Tagifiables, ReprHtml, etc.).
   - empty → delegate to the displayhook that was installed *before* ours
     (preserves REPL/Jupyter behavior, anything else built on displayhook).
3. ``__enter__`` calls ``push(self)`` to capture a ``Token``; ``__exit__``
   calls ``pop(token)`` to restore the prior stack snapshot. The Token-based
   reset is robust to exceptions in the ``with`` body.

This module is private. ``AllowsChildren`` (in ``_children.py``) and
``CtxTag`` (in ``_ctx_tag.py``) are the only callers.
"""

from __future__ import annotations

import contextvars
import sys
from typing import Any, Callable

from htmltools import wrap_displayhook_handler

_stack: contextvars.ContextVar[tuple[Any, ...]] = contextvars.ContextVar(
    "shinyui_parent_stack", default=()
)
_installed: bool = False
_prev_displayhook: Callable[[object], None] | None = None


def _dispatch(x: object) -> None:
    stack = _stack.get()
    if stack:
        wrap_displayhook_handler(stack[-1].append)(x)
    else:
        assert _prev_displayhook is not None
        _prev_displayhook(x)


def _ensure_installed() -> None:
    global _installed, _prev_displayhook
    if not _installed:
        _prev_displayhook = sys.displayhook
        sys.displayhook = _dispatch
        _installed = True


def push(parent: Any) -> contextvars.Token[tuple[Any, ...]]:
    """Push ``parent`` onto the current task's parent stack and return the
    reset Token. Lazily installs the global displayhook shim on first call.
    """
    _ensure_installed()
    return _stack.set(_stack.get() + (parent,))


def pop(token: contextvars.Token[tuple[Any, ...]]) -> None:
    """Restore the stack to its snapshot at the time ``token`` was issued."""
    _stack.reset(token)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pkg-py/tests/shinyui/test_ctx_stack.py::test_push_pop_isolated_stack pkg-py/tests/shinyui/test_ctx_stack.py::test_displayhook_appends_to_stack_tip pkg-py/tests/shinyui/test_ctx_stack.py::test_displayhook_fall_through_outside_with_block -v`

Expected: 3 PASS. Note: `test_displayhook_appends_to_stack_tip` passes because the existing `AllowsChildren.__enter__` / `__exit__` still no-ops at this point — *but* the test only uses `sys.displayhook(...)` directly, which means it doesn't depend on `AllowsChildren` yet. Wait — actually it does, because we're entering `sui.card(id="m")`. Let me re-check:

Re-reading the test: `with sui.card(id="m") as c:` enters the existing no-op `__enter__`, which does NOT call `push`. So the stack stays empty, displayhook falls through, and `c.children` stays empty. Test FAILS at this stage.

Revise: this test will pass only after Task 2 wires `AllowsChildren` to `push`/`pop`. Move it to Task 2.

Replace the test file with a smaller Task-1 version (only the stack-internal test and the fall-through test, both of which call `push`/`pop` directly or `_ensure_installed` directly):

Re-create `pkg-py/tests/shinyui/test_ctx_stack.py`:

```python
"""Tests for shinyui's parent-tag context stack (issue #70, Stage A).

Direct push/pop and displayhook tests live here; the AllowsChildren
integration tests live in test_allows_children.py.
"""

from __future__ import annotations

import sys

import shinyui as sui
from htmltools import tags


def test_push_pop_isolated_stack() -> None:
    """push/pop maintain a stack via Token-based reset."""
    from shinyui._ctx_stack import _stack, pop, push

    assert _stack.get() == ()
    parent_a = sui.card(id="a")
    token_a = push(parent_a)
    assert _stack.get() == (parent_a,)
    parent_b = sui.card(id="b")
    token_b = push(parent_b)
    assert _stack.get() == (parent_a, parent_b)
    pop(token_b)
    assert _stack.get() == (parent_a,)
    pop(token_a)
    assert _stack.get() == ()


def test_displayhook_routes_to_stack_tip_via_push() -> None:
    """sys.displayhook(value) while a parent is on the stack appends to it."""
    from shinyui._ctx_stack import pop, push

    c = sui.card(id="m")
    token = push(c)
    try:
        sys.displayhook(tags.p("hi"))
    finally:
        pop(token)
    assert len(c.children) == 1


def test_displayhook_fall_through_outside_with_block() -> None:
    """sys.displayhook(value) with empty stack delegates to prior displayhook."""
    from shinyui._ctx_stack import _ensure_installed

    _ensure_installed()

    seen: list[object] = []
    import shinyui._ctx_stack as cs

    original_prev = cs._prev_displayhook
    cs._prev_displayhook = seen.append
    try:
        sys.displayhook("untargeted")
    finally:
        cs._prev_displayhook = original_prev

    assert seen == ["untargeted"]
```

Re-run: `uv run pytest pkg-py/tests/shinyui/test_ctx_stack.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/_ctx_stack.py pkg-py/tests/shinyui/test_ctx_stack.py
git commit -m "feat(shinyui): parent-tag context stack with lazy sys.displayhook shim (#70)"
```

---

## Task 2: Wire `AllowsChildren` into the stack

**Files:**
- Modify: `pkg-py/src/shinyui/_children.py`
- Modify: `pkg-py/tests/shinyui/test_allows_children.py`

- [ ] **Step 1: Write the failing test**

Replace the existing `test_bare_tag_in_with_block_is_not_auto_collected` in `pkg-py/tests/shinyui/test_allows_children.py` with new behaviors:

```python
from __future__ import annotations

import sys

import shinyui as sui
from htmltools import tags


def test_card_append_mutates_children():
    c = sui.card(id="m")
    c.append(tags.p("hi"))
    assert len(c.children) == 1


def test_card_with_block_collects_via_append():
    with sui.card(id="m") as c:
        c.append(tags.p("inside"))
    assert len(c.children) == 1


def test_accordion_panel_can_be_nested_in_accordion():
    a = sui.accordion(
        sui.accordion_panel("A", tags.p("a-body")),
        sui.accordion_panel("B", tags.p("b-body")),
        id="acc",
    )
    assert len(a.children) == 2


def test_with_block_collects_via_displayhook() -> None:
    """Direct sys.displayhook calls inside a with-block route to the parent."""
    with sui.card(id="m") as c:
        sys.displayhook(tags.p("collected"))
    assert len(c.children) == 1
    assert c.children[0].name == "p"


def test_nested_with_routes_to_innermost_parent() -> None:
    """Nested AllowsChildren context managers form a proper stack."""
    with sui.card(id="m") as c:
        with sui.accordion(id="acc") as acc:
            with sui.accordion_panel("A") as panel:
                sys.displayhook(tags.p("in panel"))
            sys.displayhook(panel)
        sys.displayhook(acc)
    assert len(c.children) == 1 and c.children[0] is acc
    assert len(acc.children) == 1 and acc.children[0] is panel
    assert len(panel.children) == 1
    assert panel.children[0].name == "p"


def test_sequential_with_blocks_do_not_leak() -> None:
    """After exiting a with-block, the stack is fully restored."""
    with sui.card(id="m1") as c1:
        sys.displayhook(tags.p("one"))
    with sui.card(id="m2") as c2:
        sys.displayhook(tags.p("two"))
    assert len(c1.children) == 1
    assert len(c2.children) == 1
    # Stack must be empty after both blocks.
    from shinyui._ctx_stack import _stack
    assert _stack.get() == ()


def test_bare_string_is_collected() -> None:
    """wrap_displayhook_handler coerces bare strings into TagChildren."""
    with sui.card(id="m") as c:
        sys.displayhook("Hello, world!")
    assert c.children == ["Hello, world!"]


def test_none_and_ellipsis_are_filtered() -> None:
    """wrap_displayhook_handler drops None and ... per htmltools semantics."""
    with sui.card(id="m") as c:
        sys.displayhook(None)
        sys.displayhook(...)
        sys.displayhook("kept")
    assert c.children == ["kept"]
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_allows_children.py -v`
Expected: 3 PASS (the pre-existing tests), 5 FAIL (the new tests, because `AllowsChildren.__enter__` does not call `push` yet).

- [ ] **Step 3: Write minimal implementation**

Replace `pkg-py/src/shinyui/_children.py`:

```python
"""AllowsChildren — mixin for components that accept children.

Mixin protocol:
  - Subclasses MUST call `super().__init__(**kwargs)` first in their __init__.
  - `AllowsChildren.__init__` claims positional args as children and forwards
    the remaining kwargs up the MRO.

Context-manager protocol (issue #70):
  - `__enter__` pushes self onto the parent-tag stack and returns self.
  - `__exit__` restores the stack to its prior snapshot via the Token captured
    in __enter__.

While a parent is on the stack, any value reaching ``sys.displayhook`` is
routed to ``self.append`` via ``htmltools.wrap_displayhook_handler``. This
fires automatically in REPL / Jupyter / Quarto / Shiny Express
(``@expressify``) — anywhere bare expression statements are displayed.
In plain Python script bodies, callers compose children positionally instead.
"""

from __future__ import annotations

import contextvars
from typing import Any

from htmltools import TagChild
from typing_extensions import Self

from ._ctx_stack import pop, push


class AllowsChildren:
    children: list[TagChild]
    _ctx_token: contextvars.Token[tuple[Any, ...]]

    def __init__(self, *children: TagChild, **kwargs: Any) -> None:
        self.children = list(children)
        super().__init__(**kwargs)

    def append(self, child: TagChild) -> Self:
        self.children.append(child)
        return self

    def __enter__(self) -> Self:
        self._ctx_token = push(self)
        return self

    def __exit__(self, *exc: object) -> None:
        pop(self._ctx_token)
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_allows_children.py -v`
Expected: 8 PASS (3 pre-existing + 5 new).

Also run the full shinyui test suite to confirm no regressions:

Run: `uv run pytest pkg-py/tests/shinyui/ -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/_children.py pkg-py/tests/shinyui/test_allows_children.py
git commit -m "feat(shinyui): AllowsChildren pushes onto parent-tag stack on __enter__ (#70)"
```

---

## Task 3: `CtxTag` — `htmltools.Tag` subclass with contextvar-aware `__enter__`

**Files:**
- Create: `pkg-py/src/shinyui/_ctx_tag.py`
- Modify: `pkg-py/src/shinyui/__init__.py`
- Modify: `pkg-py/tests/shinyui/test_public_exports.py`
- Add to: `pkg-py/tests/shinyui/test_ctx_stack.py`

- [ ] **Step 1: Write the failing test**

Append to `pkg-py/tests/shinyui/test_ctx_stack.py`:

```python
def test_ctx_tag_as_context_manager_collects_children() -> None:
    """CtxTag.__enter__ pushes onto the stack so bare expressions collect."""
    outer = sui.CtxTag("div")
    with outer as d:
        sys.displayhook(sui.CtxTag("h1", "Title"))
        sys.displayhook("body text")
    assert len(d.children) == 2
    assert d.children[0].name == "h1"
    assert d.children[1] == "body text"


def test_ctx_tag_outside_with_block_behaves_like_tag() -> None:
    """Constructing a CtxTag outside any with-block does not touch the stack."""
    t = sui.CtxTag("span", "ok")
    assert t.name == "span"
    assert "ok" in list(t.children)


def test_ctx_tag_overrides_htmltools_displayhook_swap() -> None:
    """CtxTag.__enter__ must NOT do htmltools' global sys.displayhook swap.

    htmltools.Tag.__enter__ sets self.prev_displayhook; if our subclass
    delegates to super().__enter__, that side-effect would happen. Verify
    it does not."""
    t = sui.CtxTag("div")
    with t:
        pass
    assert t.prev_displayhook is None
```

- [ ] **Step 2: Add the public-export test**

Modify `pkg-py/tests/shinyui/test_public_exports.py`:

```python
def test_public_exports():
    import shinyui as sui

    # Base/mixin class names (PascalCase, same as shiny.render.Renderer)
    assert sui.UiComponent
    assert sui.UiInput and sui.UiOutput and sui.UiLayout
    assert sui.HasInputValue and sui.Updatable and sui.AllowsChildren

    # Concrete classes (snake_case, same as shiny.render.data_frame)
    assert isinstance(sui.input_slider, type)
    assert isinstance(sui.input_select, type)
    assert isinstance(sui.input_action_button, type)
    assert isinstance(sui.output_code, type)
    assert isinstance(sui.output_plot, type)
    assert isinstance(sui.card, type)
    assert isinstance(sui.accordion, type)
    assert isinstance(sui.accordion_panel, type)

    # Tag-as-CM (issue #70)
    assert isinstance(sui.CtxTag, type)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_ctx_stack.py::test_ctx_tag_as_context_manager_collects_children pkg-py/tests/shinyui/test_ctx_stack.py::test_ctx_tag_outside_with_block_behaves_like_tag pkg-py/tests/shinyui/test_ctx_stack.py::test_ctx_tag_overrides_htmltools_displayhook_swap pkg-py/tests/shinyui/test_public_exports.py -v`

Expected: 4 FAIL — `AttributeError: module 'shinyui' has no attribute 'CtxTag'`.

- [ ] **Step 4: Write minimal implementation**

Create `pkg-py/src/shinyui/_ctx_tag.py`:

```python
"""CtxTag — `htmltools.Tag` subclass with contextvar-aware ``__enter__``.

Stage-A demonstration of the parent-tag context stack on a plain Tag (no
Shiny dependency). The Stage B target is to port these ``__enter__`` /
``__exit__`` overrides onto ``htmltools.Tag`` itself in py-htmltools.

Overrides ``Tag.__enter__`` / ``Tag.__exit__`` (which swap ``sys.displayhook``
globally without a contextvar) with the async-safe contextvar variant.
Outside a ``with`` block, ``CtxTag`` behaves exactly like ``Tag``.
"""

from __future__ import annotations

import contextvars
from typing import Any

from htmltools import Tag
from typing_extensions import Self

from ._ctx_stack import pop, push


class CtxTag(Tag):
    _ctx_token: contextvars.Token[tuple[Any, ...]]

    def __enter__(self) -> Self:  # type: ignore[override]
        self._ctx_token = push(self)
        return self

    def __exit__(self, *exc: object) -> None:
        pop(self._ctx_token)
```

Modify `pkg-py/src/shinyui/__init__.py`:

```python
"""shinyui — prototype class-per-component UI hierarchy.

See docs/superpowers/specs/2026-05-13-shinyui-metadata-consolidation-design.md.
"""

from ._accordion import accordion
from ._accordion_panel import accordion_panel
from ._base import UiComponent
from ._bookmark import lookup_component
from ._card import card
from ._children import AllowsChildren
from ._ctx_tag import CtxTag
from ._input_action_button import input_action_button
from ._input_select import input_select
from ._input_slider import input_slider
from ._input_value import HasInputValue
from ._output_code import output_code
from ._output_plot import output_plot
from ._roles import UiInput, UiLayout, UiOutput
from ._updatable import Updatable

__all__ = [
    "AllowsChildren",
    "CtxTag",
    "HasInputValue",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "Updatable",
    "accordion",
    "accordion_panel",
    "card",
    "input_action_button",
    "input_select",
    "input_slider",
    "lookup_component",
    "output_code",
    "output_plot",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_ctx_stack.py pkg-py/tests/shinyui/test_public_exports.py -v`

Expected: All PASS (6 in test_ctx_stack.py + test_public_exports.py).

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyui/_ctx_tag.py pkg-py/src/shinyui/__init__.py pkg-py/tests/shinyui/test_ctx_stack.py pkg-py/tests/shinyui/test_public_exports.py
git commit -m "feat(shinyui): CtxTag — Tag subclass that joins the parent-tag stack (#70)"
```

---

## Task 4: Concurrent-task isolation test

**Files:**
- Add to: `pkg-py/tests/shinyui/test_ctx_stack.py`

- [ ] **Step 1: Write the failing test**

Append to `pkg-py/tests/shinyui/test_ctx_stack.py`:

```python
import asyncio

import pytest


@pytest.mark.asyncio
async def test_concurrent_tasks_have_isolated_stacks() -> None:
    """Two asyncio tasks each in their own with-block must not pollute each
    other's parent. ContextVar copies at task creation time, so each task
    sees an empty stack at the start and its own parent thereafter."""

    started_a = asyncio.Event()
    started_b = asyncio.Event()
    finish = asyncio.Event()

    card_a: sui.card | None = None
    card_b: sui.card | None = None

    async def task_a() -> None:
        nonlocal card_a
        with sui.card(id="A") as ca:
            card_a = ca
            sys.displayhook(tags.p("a1"))
            started_a.set()
            await started_b.wait()
            sys.displayhook(tags.p("a2"))
            await finish.wait()
            sys.displayhook(tags.p("a3"))

    async def task_b() -> None:
        nonlocal card_b
        await started_a.wait()
        with sui.card(id="B") as cb:
            card_b = cb
            sys.displayhook(tags.p("b1"))
            started_b.set()
            await asyncio.sleep(0)
            sys.displayhook(tags.p("b2"))

    a = asyncio.create_task(task_a())
    b = asyncio.create_task(task_b())
    await b
    finish.set()
    await a

    assert card_a is not None and card_b is not None
    assert len(card_a.children) == 3
    assert all(c.children[0] == f"a{i}" for i, c in enumerate(card_a.children, 1))
    assert len(card_b.children) == 2
    assert all(c.children[0] == f"b{i}" for i, c in enumerate(card_b.children, 1))
```

- [ ] **Step 2: Run test to verify it passes (no impl change needed — Task 1 already used ContextVar)**

Run: `uv run pytest pkg-py/tests/shinyui/test_ctx_stack.py::test_concurrent_tasks_have_isolated_stacks -v`

Expected: PASS. The `ContextVar` already isolates per-task; this test is a guard against future regressions.

If FAIL with `pytest_asyncio` not installed: check `pyproject.toml`'s test deps. Run:

```bash
grep -n "pytest-asyncio\|pytest_asyncio" pyproject.toml
```

If absent, add `pytest-asyncio` to the dev dependency group (the shinyui tests don't currently use async, so this would be a first). Skip this test and document in the commit message if adding the dep is out of scope; otherwise add and re-run.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/tests/shinyui/test_ctx_stack.py
git commit -m "test(shinyui): assert per-task isolation of the parent-tag stack (#70)"
```

---

## Task 5: End-to-end `@expressify` snapshot test

**Files:**
- Add to: `pkg-py/tests/shinyui/test_ctx_stack.py`

- [ ] **Step 1: Write the failing test**

Append to `pkg-py/tests/shinyui/test_ctx_stack.py`:

```python
def test_expressify_with_blocks_match_positional_form() -> None:
    """The same UI tree built two ways must render byte-identical HTML.

    Positional form: explicit ``card(accordion(panel(slider), ...))`` nesting.
    Express form: ``@expressify`` rewrites bare expression statements into
    ``sys.displayhook(...)`` calls; our shim routes them to the active parent.
    """
    positional = sui.card(
        sui.accordion(
            sui.accordion_panel("A", sui.input_slider("n", "N", 1, 10, 5)),
            id="acc",
        ),
        id="m",
    )

    @expressify
    def build() -> sui.card:
        with sui.card(id="m") as c:
            with sui.accordion(id="acc"):
                with sui.accordion_panel("A"):
                    sui.input_slider("n", "N", 1, 10, 5)
        return c

    express_form = build()

    assert str(positional.tagify()) == str(express_form.tagify())
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest pkg-py/tests/shinyui/test_ctx_stack.py::test_expressify_with_blocks_match_positional_form -v`

Expected: PASS. All infrastructure is in place from Tasks 1–3.

If FAIL with mismatched HTML: print both sides (`pytest -v --capture=no -k expressify`) and diff. Likely culprits:
- Trailing-space / whitespace differences in `Tag.tagify()` — unlikely; htmltools is deterministic.
- Order of children — verify the express form's `c.children` matches the positional form's.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/tests/shinyui/test_ctx_stack.py
git commit -m "test(shinyui): @expressify form produces byte-identical HTML to positional (#70)"
```

---

## Task 6: Example app `15-shinyui-with-blocks`

**Files:**
- Create: `examples/app-py/15-shinyui-with-blocks/app.py`

- [ ] **Step 1: Create the example app**

Create `examples/app-py/15-shinyui-with-blocks/app.py`:

```python
"""End-to-end demo of shinyui's class-per-component hierarchy in ``with`` form.

This is the Express-with-blocks variant of ``14-unified-ui-prototype/``. The
two apps produce the same UI tree. Compare:

  - ``14-unified-ui-prototype/app.py`` — positional composition:
    ``card(accordion(accordion_panel("Settings", n_slider, ...), ...), ...)``
  - This file — context-manager composition:
    ``with card(): with accordion(): with accordion_panel("Settings"): ...``

Both rely on ``@expressify`` (Shiny Express's default for ``app.py``) so bare
expression statements get rewritten to ``sys.displayhook(...)`` calls. The
shinyui parent-tag context stack (issue #70) routes those values to the
innermost active ``with`` parent.
"""

from __future__ import annotations

import shinyui as su
from shiny import reactive
from shiny import ui as _sui
from shiny.express import render, ui

# --- Components -------------------------------------------------------------
# Components without children are constructed at module top-level so the
# server-side accessors (``n_slider.value()``, etc.) bind to instances we hold.
n_slider = su.input_slider("n", "Sample size", 10, 1000, 100)
seed_slider = su.input_slider("seed", "Seed", 1, 1000, 42)
dist_select = su.input_select(
    "dist",
    "Distribution",
    {"normal": "Normal", "uniform": "Uniform"},
)
plot_handle = su.output_plot("plot", click=True, brush=True)
open_all_btn = su.input_action_button("open_all", "Open all panels")
close_all_btn = su.input_action_button("close_all", "Close all panels")
summary_code = su.output_code("summary")
diag_code = su.output_code("diag")

# --- Page ------------------------------------------------------------------
ui.page_opts(title="shinyui Stage A — with-block form")

# Build the UI tree with `with` blocks. Express's @expressify rewrite turns
# each bare expression below into `sys.displayhook(value)`; shinyui's parent
# stack routes them to the active `with` parent.
with su.card(id="main_card", full_screen=False) as main_card:
    _sui.layout_column_wrap(open_all_btn, close_all_btn, width=1 / 2)
    with su.accordion(id="acc", open="Settings") as acc:
        with su.accordion_panel("Settings"):
            n_slider
            dist_select
            seed_slider
        with su.accordion_panel("Diagnostics"):
            summary_code
            diag_code
    plot_handle


# --- Renderers -------------------------------------------------------------
# ``ui.hold()`` suppresses Express's default auto-placement so each renderer
# binds to its id-matching output placed inside the accordion / card above.
with ui.hold():

    @render.code
    def summary():
        return (
            f"n     = {n_slider.value()}\n"
            f"dist  = {dist_select.value()}\n"
            f"seed  = {seed_slider.value()}\n"
            f"open  = {acc.open_panels()}\n"
            f"fs    = {main_card.full_screen_value()}\n"
        )

    @render.code
    def diag():
        return (
            f"click = {plot_handle.click_value()}\n"
            f"brush = {plot_handle.brush_value()}\n"
        )

    @render.plot
    def plot():
        import matplotlib.pyplot as plt
        import numpy as np

        rng = np.random.default_rng(seed_slider.value())
        n = n_slider.value()
        if dist_select.value() == "normal":
            x = rng.standard_normal(n)
            y = rng.standard_normal(n)
        else:
            x = rng.uniform(-2, 2, n)
            y = rng.uniform(-2, 2, n)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(x, y, s=12, alpha=0.6)
        ax.set_title(f"{dist_select.value()} sample, n={n}, seed={seed_slider.value()}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, alpha=0.3)
        return fig


# --- Reactive effects ------------------------------------------------------
@reactive.effect
@reactive.event(open_all_btn.clicked, ignore_init=True)
def _open_all_panels():
    acc.update(open=("Settings", "Diagnostics"))


@reactive.effect
@reactive.event(close_all_btn.clicked, ignore_init=True)
def _close_all_panels():
    acc.update(open=False)
```

- [ ] **Step 2: Confirm the app starts**

Run: `uv run shiny run --port 0 examples/app-py/15-shinyui-with-blocks/app.py --launch-browser` in a separate terminal (or `--no-launch-browser` for headless CI-style check). Wait for `Application startup complete`. Stop with Ctrl-C.

If FAIL: the most likely cause is the bare `n_slider` line inside `with su.accordion_panel("Settings"):` not being collected. Confirm `@expressify` is in effect by checking that the top-level `with su.card(id="main_card", ...) as main_card:` line has its bare body expressions routed (you'll see the rendered card with the layout, accordion, and plot).

- [ ] **Step 3: Commit**

```bash
git add examples/app-py/15-shinyui-with-blocks/app.py
git commit -m "feat(examples): with-block shinyui variant of 14-unified-ui-prototype (#70)"
```

---

## Task 7: Final verification

**Files:** none

- [ ] **Step 1: Run the full Python check suite**

Run: `make py-check`

Expected: format check + type check + all tests PASS. Resolve any failures inline.

- [ ] **Step 2: Run a quick lint of the example app**

Run: `uv run ruff check examples/app-py/15-shinyui-with-blocks/app.py`

Expected: PASS. Common warnings to expect-and-allow:
- `B018` "Found useless expression" — these are the bare expressions that `@expressify` rewrites. The existing `14-unified-ui-prototype/app.py` is similarly flagged or uses `# noqa`. Match its style.

If B018 fires and the existing `14-unified-ui-prototype/app.py` does NOT have `# noqa` markers, check `pyproject.toml` for an existing ruff ignore covering the examples directory.

- [ ] **Step 3: Spot-check by running the example app once more**

Run: `uv run shiny run --port 0 examples/app-py/15-shinyui-with-blocks/app.py --no-launch-browser` (briefly; stop with Ctrl-C). Confirm startup is clean.

- [ ] **Step 4: Commit any cleanup**

If `make py-check` made formatting changes:

```bash
git add -u
git commit -m "style: apply ruff format after #70 implementation"
```

- [ ] **Step 5: Push and open PR**

```bash
git push -u origin schloerke/issue-70
gh pr create --base main --title "feat: tag-as-context-manager for shinyui (#70)" --body "$(cat <<'EOF'
## Summary
- Adds a per-task `ContextVar` parent stack + lazy `sys.displayhook` shim in `shinyui/_ctx_stack.py`.
- Wires `AllowsChildren.__enter__/__exit__` to push/pop the stack — `card`, `accordion`, `accordion_panel` light up as context managers with no per-class changes.
- Adds `shinyui.CtxTag` — `htmltools.Tag` subclass that participates in the same stack; Stage A demo of what Stage B ports onto `Tag` itself.
- Adds `examples/app-py/15-shinyui-with-blocks/app.py` — the `with`-block form of the existing `14-unified-ui-prototype/` demo.

Spec: `docs/superpowers/specs/2026-05-15-tag-context-manager-design.md`.
Issue: #70 (umbrella #68).

## Test plan
- [ ] `make py-check` passes.
- [ ] `pkg-py/tests/shinyui/test_ctx_stack.py` covers: push/pop, displayhook routing, fall-through, CtxTag, per-task isolation, `@expressify` snapshot.
- [ ] `examples/app-py/15-shinyui-with-blocks/app.py` runs in a browser and behaves identically to `14-unified-ui-prototype/`.
EOF
)"
```

---

## Self-Review

**Spec coverage:**
- Mechanism (`_ctx_stack.py`) → Task 1.
- `AllowsChildren.__enter__/__exit__` wired → Task 2.
- `CtxTag` subclass → Task 3.
- Concurrency / per-task isolation → Task 4.
- `@expressify` snapshot acceptance → Task 5.
- Example app → Task 6.
- Final verification (`make py-check`) → Task 7.

All acceptance criteria covered.

**Placeholder scan:** Every step has a concrete file path and code block. The "if FAIL" guidance in Task 4 step 2 is a real diagnostic, not a placeholder.

**Type/name consistency:**
- `push(parent)` returns `contextvars.Token[tuple[Any, ...]]` everywhere it's referenced (`_ctx_stack.py`, `_children.py`, `_ctx_tag.py`).
- `_stack`, `_installed`, `_prev_displayhook` are the consistent module-private names.
- `AllowsChildren._ctx_token` and `CtxTag._ctx_token` use the same name across both classes.
- `_dispatch` is the displayhook shim everywhere (not "dispatch" or "shim").
