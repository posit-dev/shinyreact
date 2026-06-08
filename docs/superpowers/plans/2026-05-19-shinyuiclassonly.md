# shinyuiclassonly Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a sibling `shinyuiclassonly` Python package that mirrors `shinyui`'s class hierarchy but drops all session-bound machinery, plus two paired examples (16 Core, 17 Express) and CLAUDE.md updates.

**Architecture:** Third top-level package under `pkg-py/src/shinyuiclassonly/` sharing the same wheel as `shinyreact` and `shinyui`. Same component vocabulary and role hierarchy as `shinyui` (`UiComponent`, `UiInput`, `UiOutput`, `UiLayout`, `AllowsChildren`, parent-tag context stack, `CtxTag`). Components are pure `Tagifiable` objects with `tagify()` delegating to `shiny.ui.*`; no `_session` capture, no `.value()`/`.update()`/`.click_value()`, no input-handler or bookmark registration, no `reactive_calc_method`. `render_plot` keeps `auto_output_ui()` (returns the `output_plot` instance directly, no `.tagify()`).

**Tech Stack:** Python 3.10+, `shiny>=1.2.0`, `htmltools>=0.6.0`, hatchling, pyright, ruff, pytest, pytest-asyncio.

**Spec:** `docs/superpowers/specs/2026-05-19-shinyuiclassonly-design.md`

---

## Reference: what to keep verbatim vs. strip from shinyui

When a task says "port from `shinyui`", that means:

- **Verbatim** (drop the `shinyui` docstring header that references `_session` if any): `_ctx_stack.py`, `_ctx_tag.py`.
- **Trim** (remove session/value/update/handler/bookmark/reactive_calc_method code, keep tagify(), keep overload signatures, keep markup forwarding): every concrete component file.

The single source of truth for what gets removed is the "What's kept vs. dropped" table in the spec.

---

### Task 1: Scaffold the package and wire the build

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/__init__.py`
- Create: `pkg-py/tests/shinyuiclassonly/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1.1: Create empty package skeleton**

```bash
mkdir -p pkg-py/src/shinyuiclassonly pkg-py/tests/shinyuiclassonly
```

- [ ] **Step 1.2: Create the placeholder `__init__.py`**

Write `pkg-py/src/shinyuiclassonly/__init__.py`:

```python
"""shinyuiclassonly — class-per-component UI hierarchy, stripped of session machinery.

A smaller delta from existing shiny.ui behavior than shinyui: the class
hierarchy, AllowsChildren + parent-tag context stack, and Core/Express
overloads, with no session capture, no `.value()`/`.update()` accessors,
no input-handler or bookmark registration. Server code reads inputs via
`input.<id>()` and pushes updates via `shiny.ui.update_*` the usual way.

See docs/superpowers/specs/2026-05-19-shinyuiclassonly-design.md.
"""
```

(`__all__` and re-exports get added incrementally as each component lands.)

- [ ] **Step 1.3: Create the tests-package marker**

Write `pkg-py/tests/shinyuiclassonly/__init__.py` as an empty file:

```python
```

- [ ] **Step 1.4: Wire `pyproject.toml`**

In `pyproject.toml`:

1. Extend `[tool.hatch.build.targets.wheel].packages`:

```toml
[tool.hatch.build.targets.wheel]
packages = [
    "pkg-py/src/shinyreact",
    "pkg-py/src/shinyui",
    "pkg-py/src/shinyuiclassonly",
]
```

2. Extend `[tool.pyright].include`:

```toml
[tool.pyright]
include = [
    "pkg-py/src/shinyreact",
    "pkg-py/src/shinyui",
    "pkg-py/src/shinyuiclassonly",
]
```

3. Extend `[tool.ruff.lint.per-file-ignores]`:

```toml
[tool.ruff.lint.per-file-ignores]
"pkg-py/src/shinyui/**/*.py" = ["N801"]
"pkg-py/src/shinyuiclassonly/**/*.py" = ["N801"]
```

- [ ] **Step 1.5: Verify the package imports**

Run: `uv run python -c "import shinyuiclassonly; print(shinyuiclassonly.__doc__.splitlines()[0])"`
Expected output:
```
shinyuiclassonly — class-per-component UI hierarchy, stripped of session machinery.
```

- [ ] **Step 1.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly pkg-py/tests/shinyuiclassonly pyproject.toml
git commit -m "feat(shinyuiclassonly): scaffold empty package and wire build"
```

---

### Task 2: `UiComponent` base class

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_base.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_base.py`

- [ ] **Step 2.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_base.py`:

```python
from __future__ import annotations

import pytest
from htmltools import tags
from shinyuiclassonly._base import UiComponent


class _Dummy(UiComponent):
    """Minimal concrete subclass for testing."""

    def tagify(self):
        return tags.div("dummy")


def test_uicomponent_is_abstract():
    with pytest.raises(TypeError):
        UiComponent()  # type: ignore[abstract]


def test_uicomponent_concrete_subclass_constructs():
    c = _Dummy()
    assert c.tagify().name == "div"


def test_uicomponent_html_dependencies_default_empty():
    assert _Dummy.html_dependencies == ()


def test_uicomponent_has_no_session_attribute():
    """shinyuiclassonly drops all session machinery."""
    c = _Dummy()
    assert not hasattr(c, "_session")
    assert not hasattr(c, "_require_session")
    assert not hasattr(c, "_read_input")


def test_uicomponent_does_not_support_context_manager_protocol():
    """Subclasses without AllowsChildren are not context managers."""
    c = _Dummy()
    with pytest.raises(TypeError, match=r"context manager protocol"):
        with c:  # noqa: B017
            pass
```

- [ ] **Step 2.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_base.py -v`
Expected: FAIL (no `_base.py` yet).

- [ ] **Step 2.3: Implement `_base.py`**

Write `pkg-py/src/shinyuiclassonly/_base.py`:

```python
"""UiComponent — abstract base for the shinyuiclassonly class hierarchy.

This is the structure-only sibling of ``shinyui.UiComponent``. It carries
only the bits that affect the class hierarchy:

  - ``html_dependencies`` ClassVar (default ``()``)
  - abstract :meth:`tagify` returning a ``Tag``

Deliberately omitted (the "no session" delta vs. ``shinyui``):

  - no ``_session`` attribute captured in ``__init__``
  - no ``_require_session(for_op=...)``
  - no ``_read_input(suffix="")``

Context-manager protocol (``__enter__`` / ``__exit__``) is declared only
on :class:`shinyuiclassonly.AllowsChildren`. Subclasses that don't inherit
``AllowsChildren`` will raise a TypeError if used as ``with ...:``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from htmltools import HTMLDependency, Tag


class UiComponent(ABC):
    html_dependencies: ClassVar[tuple[HTMLDependency, ...]] = ()

    @abstractmethod
    def tagify(self) -> Tag: ...
```

- [ ] **Step 2.4: Run tests to verify they pass**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_base.py -v`
Expected: PASS (5 tests).

- [ ] **Step 2.5: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_base.py pkg-py/tests/shinyuiclassonly/test_base.py
git commit -m "feat(shinyuiclassonly): UiComponent base — abstract tagify, no session"
```

---

### Task 3: Role marker classes — `UiInput`, `UiOutput`, `UiLayout`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_roles.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_roles.py`

- [ ] **Step 3.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_roles.py`:

```python
from __future__ import annotations

from htmltools import tags
from shinyuiclassonly._base import UiComponent
from shinyuiclassonly._roles import UiInput, UiLayout, UiOutput


class _MyInput(UiInput):
    def tagify(self):
        return tags.div()


class _MyOutput(UiOutput):
    def tagify(self):
        return tags.div()


class _MyLayout(UiLayout):
    def tagify(self):
        return tags.div()


def test_roles_are_uicomponent_subclasses():
    assert issubclass(UiInput, UiComponent)
    assert issubclass(UiOutput, UiComponent)
    assert issubclass(UiLayout, UiComponent)


def test_roles_have_no_extra_abstract_methods():
    """UiInput has no abstract value() method (delta vs. shinyui)."""
    _MyInput()
    _MyOutput()
    _MyLayout()


def test_role_inheritance_independent():
    """Roles are sibling categories, not a chain."""
    assert not issubclass(UiInput, UiOutput)
    assert not issubclass(UiOutput, UiLayout)
    assert not issubclass(UiLayout, UiInput)
```

- [ ] **Step 3.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_roles.py -v`
Expected: FAIL (no `_roles.py`).

- [ ] **Step 3.3: Implement `_roles.py`**

Write `pkg-py/src/shinyuiclassonly/_roles.py`:

```python
"""Semantic role classes — UiInput, UiOutput, UiLayout.

These are pure marker subclasses of :class:`UiComponent`. They indicate
the component's primary purpose (input control, output placeholder,
layout container) but carry no behavior of their own.

This is the structure-only sibling of ``shinyui._roles``. The shinyui
equivalents declare an abstract ``UiInput.value()`` and rely on
``HasInputValue`` for input-handler / bookmark registration; here all of
that is gone — these classes are bare markers.
"""

from __future__ import annotations

from ._base import UiComponent


class UiInput(UiComponent):
    """Marker: primarily a user-input control."""


class UiOutput(UiComponent):
    """Marker: primarily a server-rendered output."""


class UiLayout(UiComponent):
    """Marker: primarily a container."""
```

- [ ] **Step 3.4: Run tests to verify they pass**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_roles.py -v`
Expected: PASS (3 tests).

- [ ] **Step 3.5: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_roles.py pkg-py/tests/shinyuiclassonly/test_roles.py
git commit -m "feat(shinyuiclassonly): UiInput / UiOutput / UiLayout marker classes"
```

---

### Task 4: Parent-tag context stack (`_ctx_stack.py`) + `CtxTag`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_ctx_stack.py`
- Create: `pkg-py/src/shinyuiclassonly/_ctx_tag.py`
- Create: `pkg-py/tests/shinyuiclassonly/conftest.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_ctx_stack.py`

This is a verbatim port from `pkg-py/src/shinyui/_ctx_stack.py` and `pkg-py/src/shinyui/_ctx_tag.py`. The module-level state (ContextVar, displayhook shim) is independent of session, so no trimming is needed.

- [ ] **Step 4.1: Write `conftest.py` with the autouse stack reset**

Write `pkg-py/tests/shinyuiclassonly/conftest.py`:

```python
"""Shared fixtures for shinyuiclassonly tests.

No session fixtures here — shinyuiclassonly is session-free.
"""

from __future__ import annotations

from typing import Iterator

import pytest


@pytest.fixture(autouse=True)
def _reset_ctx_stack() -> Iterator[None]:
    """Isolate the parent-tag context stack between tests.

    The stack lives in a process-wide ContextVar. In a sync pytest run,
    tests share the same context, so a test that forgets to pop a parent
    would dirty every subsequent test. Reset on both edges.
    """
    from shinyuiclassonly._ctx_stack import _stack

    token = _stack.set(())
    try:
        yield
    finally:
        _stack.reset(token)
```

- [ ] **Step 4.2: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_ctx_stack.py`:

```python
"""Tests for shinyuiclassonly's parent-tag context stack and CtxTag.

Verbatim parallel of pkg-py/tests/shinyui/test_ctx_stack.py, scoped to
the components shinyuiclassonly actually ships (no input_slider used
inside the expressify round-trip, since that comes later — keep this
test independent of component-class details).
"""

from __future__ import annotations

import asyncio
import sys

import pytest
import shinyuiclassonly as sui
from htmltools import tags


def test_push_pop_isolated_stack() -> None:
    from shinyuiclassonly._ctx_stack import _stack, pop, push

    assert _stack.get() == ()
    parent_a = sui.CtxTag("div", id="a")
    token_a = push(parent_a)
    try:
        assert _stack.get() == (parent_a,)
        parent_b = sui.CtxTag("div", id="b")
        token_b = push(parent_b)
        try:
            assert _stack.get() == (parent_a, parent_b)
        finally:
            pop(token_b)
        assert _stack.get() == (parent_a,)
    finally:
        pop(token_a)
    assert _stack.get() == ()


def test_displayhook_routes_to_stack_tip_via_push() -> None:
    from shinyuiclassonly._ctx_stack import pop, push

    c = sui.CtxTag("div")
    token = push(c)
    try:
        sys.displayhook(tags.p("hi"))
    finally:
        pop(token)
    assert len(c.children) == 1
    assert c.children[0].name == "p"


def test_displayhook_fall_through_outside_with_block() -> None:
    from shinyuiclassonly._ctx_stack import _ensure_installed

    _ensure_installed()

    seen: list[object] = []
    import shinyuiclassonly._ctx_stack as cs

    original_prev = cs._prev_displayhook
    cs._prev_displayhook = seen.append
    try:
        sys.displayhook("untargeted")
    finally:
        cs._prev_displayhook = original_prev

    assert seen == ["untargeted"]


def test_ctx_tag_as_context_manager_collects_children() -> None:
    outer = sui.CtxTag("div")
    with outer as d:
        sys.displayhook(sui.CtxTag("h1", "Title"))
        sys.displayhook("body text")
    assert len(d.children) == 2
    assert d.children[0].name == "h1"
    assert d.children[1] == "body text"


def test_ctx_tag_outside_with_block_behaves_like_tag() -> None:
    t = sui.CtxTag("span", "ok")
    assert t.name == "span"
    assert "ok" in list(t.children)


def test_ctx_tag_overrides_htmltools_displayhook_swap() -> None:
    t = sui.CtxTag("div")
    with t:
        pass
    assert t.prev_displayhook is None


@pytest.mark.asyncio
async def test_concurrent_tasks_have_isolated_stacks() -> None:
    started_a = asyncio.Event()
    started_b = asyncio.Event()
    finish = asyncio.Event()

    a_div: sui.CtxTag | None = None
    b_div: sui.CtxTag | None = None

    async def task_a() -> None:
        nonlocal a_div
        with sui.CtxTag("div", id="A") as da:
            a_div = da
            sys.displayhook(tags.p("a1"))
            started_a.set()
            await started_b.wait()
            sys.displayhook(tags.p("a2"))
            await finish.wait()
            sys.displayhook(tags.p("a3"))

    async def task_b() -> None:
        nonlocal b_div
        await started_a.wait()
        with sui.CtxTag("div", id="B") as db:
            b_div = db
            sys.displayhook(tags.p("b1"))
            started_b.set()
            await asyncio.sleep(0)
            sys.displayhook(tags.p("b2"))

    a = asyncio.create_task(task_a())
    b = asyncio.create_task(task_b())
    await b
    finish.set()
    await a

    assert a_div is not None and b_div is not None
    a_p = [c for c in a_div.children if hasattr(c, "name") and c.name == "p"]
    b_p = [c for c in b_div.children if hasattr(c, "name") and c.name == "p"]
    assert len(a_p) == 3
    assert len(b_p) == 2
```

(Note: this test file imports `shinyuiclassonly as sui` and uses `sui.CtxTag`, so we also need to re-export `CtxTag` from `__init__.py` in step 4.5.)

- [ ] **Step 4.3: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_ctx_stack.py -v`
Expected: FAIL (no `_ctx_stack.py`, no `CtxTag` export).

- [ ] **Step 4.4: Implement `_ctx_stack.py` (verbatim port)**

Write `pkg-py/src/shinyuiclassonly/_ctx_stack.py`:

```python
"""Parent-tag context stack — backs shinyuiclassonly's ``with``-block child collection.

Verbatim port of ``shinyui._ctx_stack``. The mechanism is session-free —
just a ContextVar-backed parent stack plus a process-wide
``sys.displayhook`` shim that routes displayed values to the active
parent's ``append`` method via ``htmltools.wrap_displayhook_handler``.

See ``shinyui/_ctx_stack.py`` for the design notes; behavior is identical.
"""

from __future__ import annotations

import contextvars
import sys
from typing import Any, Callable

from htmltools import wrap_displayhook_handler

_stack: contextvars.ContextVar[tuple[Any, ...]] = contextvars.ContextVar(
    "shinyuiclassonly_parent_stack", default=()
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


def dispatch_to_active_parent(x: Any) -> None:
    """Forward ``x`` to the active parent — the next outer ``with``-block parent
    if one exists, otherwise the displayhook that was installed before ours.
    """
    sys.displayhook(x)
```

- [ ] **Step 4.5: Implement `_ctx_tag.py` (verbatim port)**

Write `pkg-py/src/shinyuiclassonly/_ctx_tag.py`:

```python
"""CtxTag — ``htmltools.Tag`` subclass with contextvar-aware ``__enter__``.

Verbatim port of ``shinyui._ctx_tag``. Lets ``with ui.div(): ...`` route
to shinyuiclassonly's parent-tag context stack instead of relying on
htmltools' global displayhook swap. Outside a ``with`` block, ``CtxTag``
behaves exactly like ``Tag``.
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

- [ ] **Step 4.6: Re-export `CtxTag` from `__init__.py`**

Modify `pkg-py/src/shinyuiclassonly/__init__.py` to append after the docstring:

```python
from ._ctx_tag import CtxTag

__all__ = ["CtxTag"]
```

- [ ] **Step 4.7: Run tests to verify they pass**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_ctx_stack.py -v`
Expected: PASS (7 tests).

- [ ] **Step 4.8: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_ctx_stack.py \
        pkg-py/src/shinyuiclassonly/_ctx_tag.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/conftest.py \
        pkg-py/tests/shinyuiclassonly/test_ctx_stack.py
git commit -m "feat(shinyuiclassonly): parent-tag context stack and CtxTag"
```

---

### Task 5: `AllowsChildren` mixin

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_children.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_children.py`

- [ ] **Step 5.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_children.py`:

```python
from __future__ import annotations

import sys

from htmltools import tags
from shinyuiclassonly._base import UiComponent
from shinyuiclassonly._children import AllowsChildren


class _ChildBox(UiComponent, AllowsChildren):
    def tagify(self):
        return tags.div(*self.children)


def test_children_default_empty():
    b = _ChildBox()
    assert b.children == []


def test_children_from_positional_args():
    b = _ChildBox("a", "b")
    assert b.children == ["a", "b"]


def test_append_returns_self_and_mutates():
    b = _ChildBox()
    r = b.append("x")
    assert r is b
    assert b.children == ["x"]


def test_with_block_returns_self_and_collects_via_displayhook():
    with _ChildBox() as b:
        sys.displayhook(tags.p("inside"))
    assert len(b.children) == 1
    assert b.children[0].name == "p"


def test_with_block_returns_self_and_collects_via_append():
    with _ChildBox() as b:
        b.append("inside")
    assert b.children == ["inside"]


def test_outermost_with_dispatches_to_prev_displayhook():
    """When the outermost `with`-block exits with an empty stack, the
    component is forwarded via sys.displayhook so the prior displayhook
    (Express / REPL) can place it.
    """
    from shinyuiclassonly._ctx_stack import _ensure_installed

    _ensure_installed()

    seen: list[object] = []
    import shinyuiclassonly._ctx_stack as cs

    original_prev = cs._prev_displayhook
    cs._prev_displayhook = seen.append
    try:
        with _ChildBox() as b:
            sys.displayhook(tags.p("inside"))
        assert b in seen
    finally:
        cs._prev_displayhook = original_prev
```

- [ ] **Step 5.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_children.py -v`
Expected: FAIL (no `_children.py`).

- [ ] **Step 5.3: Implement `_children.py`**

Write `pkg-py/src/shinyuiclassonly/_children.py`:

```python
"""AllowsChildren — mixin for components that accept children.

Verbatim port of ``shinyui._children`` — the behavior is independent of
session state. Subclasses MUST call ``super().__init__(**kwargs)`` first.

While a parent is on the stack (entered via ``with``), any value reaching
``sys.displayhook`` is routed to ``self.append`` via
``htmltools.wrap_displayhook_handler``. This fires automatically in REPL
/ Jupyter / Quarto / Shiny Express (``@expressify``). In plain Python
script bodies, callers compose children positionally instead.
"""

from __future__ import annotations

import contextvars
from typing import Any

from htmltools import TagChild
from typing_extensions import Self

from ._ctx_stack import dispatch_to_active_parent, pop, push


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
        if exc[0] is None:
            dispatch_to_active_parent(self)
```

- [ ] **Step 5.4: Run tests to verify they pass**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_children.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5.5: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_children.py pkg-py/tests/shinyuiclassonly/test_children.py
git commit -m "feat(shinyuiclassonly): AllowsChildren mixin with __enter__/__exit__"
```

---

### Task 6: `card` layout

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_card.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_card.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 6.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_card.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui
from htmltools import tags


def test_card_tagify_basic():
    c = sui.card(tags.p("hi"), id="m")
    rendered = c.tagify()
    assert "shiny-html-output" not in str(rendered)  # not an output
    assert "main" not in str(rendered)  # placeholder check on id quirk


def test_card_id_optional():
    """shinyuiclassonly does not require id on layouts (no accessors to wire)."""
    c = sui.card(tags.p("hi"))
    assert c.id is None
    c.tagify()  # must render


def test_card_stores_full_screen_flag():
    c = sui.card(id="m", full_screen=True)
    assert c._full_screen is True


def test_card_collects_children_via_with():
    import sys

    with sui.card(id="m") as c:
        sys.displayhook(tags.p("inside"))
    assert len(c.children) == 1
    assert c.children[0].name == "p"


def test_card_positional_children():
    c = sui.card(tags.p("a"), tags.p("b"), id="m")
    assert len(c.children) == 2


def test_card_has_no_value_or_update_methods():
    """shinyuiclassonly strips accessors and update()."""
    c = sui.card(id="m")
    assert not hasattr(c, "full_screen_value")
    assert not hasattr(c, "update")


def test_card_is_uilayout_and_allows_children():
    c = sui.card(id="m")
    assert isinstance(c, sui.UiLayout)
    assert isinstance(c, sui.AllowsChildren)
```

- [ ] **Step 6.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_card.py -v`
Expected: FAIL (no `_card.py`).

- [ ] **Step 6.3: Implement `_card.py`**

Write `pkg-py/src/shinyuiclassonly/_card.py`:

```python
"""card — layout container.

Structure-only sibling of ``shinyui.card``. Same Express + Core overloads,
same ``tagify()`` delegation to ``shiny.ui.card``. The session-aware
``full_screen_value()`` reader and ``update()`` are dropped. ``id`` is
optional (no accessor needs it).
"""

from __future__ import annotations

from typing import Any, Optional, overload

from htmltools import Tag, TagChild

from ._children import AllowsChildren
from ._roles import UiLayout


class card(UiLayout, AllowsChildren):
    """Card container with optional full-screen toggle.

    No server-side accessor here. Read the full-screen state via
    ``input.<id>_full_screen()`` on the server side (shiny's card binding
    pushes that input id when ``id=`` is supplied).
    """

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
    @overload
    def __init__(
        self,
        *,
        id: Optional[str] = None,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None: ...

    # Core overload — inline positional children.
    @overload
    def __init__(
        self,
        *args: TagChild,
        id: Optional[str] = None,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None: ...

    def __init__(
        self,
        *args: TagChild,
        id: Optional[str] = None,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None:
        self.id = id
        self._full_screen = full_screen
        self.height = height
        self.max_height = max_height
        self.min_height = min_height
        self.fill = fill
        self.class_ = class_
        super().__init__(*args)

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        kwargs: dict[str, Any] = {
            "full_screen": self._full_screen,
            "fill": self.fill,
        }
        if self.id is not None:
            kwargs["id"] = self.id
        if self.height is not None:
            kwargs["height"] = self.height
        if self.max_height is not None:
            kwargs["max_height"] = self.max_height
        if self.min_height is not None:
            kwargs["min_height"] = self.min_height
        if self.class_ is not None:
            kwargs["class_"] = self.class_

        return _sui.card(*self.children, **kwargs).tagify()
```

- [ ] **Step 6.4: Re-export `card` and `UiLayout`/`AllowsChildren` from `__init__.py`**

Modify `pkg-py/src/shinyuiclassonly/__init__.py`:

```python
"""shinyuiclassonly — class-per-component UI hierarchy, stripped of session machinery.

A smaller delta from existing shiny.ui behavior than shinyui: the class
hierarchy, AllowsChildren + parent-tag context stack, and Core/Express
overloads, with no session capture, no `.value()`/`.update()` accessors,
no input-handler or bookmark registration. Server code reads inputs via
`input.<id>()` and pushes updates via `shiny.ui.update_*` the usual way.

See docs/superpowers/specs/2026-05-19-shinyuiclassonly-design.md.
"""

from ._base import UiComponent
from ._card import card
from ._children import AllowsChildren
from ._ctx_tag import CtxTag
from ._roles import UiInput, UiLayout, UiOutput

__all__ = [
    "AllowsChildren",
    "CtxTag",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "card",
]
```

- [ ] **Step 6.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_card.py -v`
Expected: PASS (7 tests).

- [ ] **Step 6.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_card.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_card.py
git commit -m "feat(shinyuiclassonly): card layout with Express+Core overloads"
```

---

### Task 7: `accordion_panel`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_accordion_panel.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_accordion_panel.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 7.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_accordion_panel.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui


def test_accordion_panel_value_defaults_to_title():
    p = sui.accordion_panel("Settings")
    assert p.value == "Settings"


def test_accordion_panel_value_can_override():
    p = sui.accordion_panel("Settings", value="settings_v")
    assert p.value == "settings_v"


def test_accordion_panel_tagify():
    p = sui.accordion_panel("A", "body text")
    rendered = p.tagify()
    assert rendered is not None


def test_accordion_panel_collects_children_via_with():
    import sys

    from htmltools import tags

    with sui.accordion_panel("Settings") as p:
        sys.displayhook(tags.p("hi"))
    assert len(p.children) == 1
    assert p.children[0].name == "p"


def test_accordion_panel_has_no_value_or_update_methods():
    """`value` is a property returning the title fallback string — it is
    NOT a session-aware accessor here (shinyui's panel has no accessor
    either, but the equivalent value() is on its parent accordion)."""
    p = sui.accordion_panel("A")
    assert isinstance(p.value, str)
    assert not hasattr(p, "update")
```

- [ ] **Step 7.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_accordion_panel.py -v`
Expected: FAIL.

- [ ] **Step 7.3: Implement `_accordion_panel.py`**

Write `pkg-py/src/shinyuiclassonly/_accordion_panel.py`:

```python
"""accordion_panel — layout child of accordion.

Structure-only sibling of ``shinyui.accordion_panel``. Same Express + Core
overloads, same ``tagify()`` delegation. Has no wire id of its own.
"""

from __future__ import annotations

from typing import overload

from htmltools import Tag, TagChild
from shiny.types import MISSING, MISSING_TYPE

from ._children import AllowsChildren
from ._roles import UiLayout


class accordion_panel(UiLayout, AllowsChildren):
    """A single collapsible panel within an :class:`accordion`."""

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
    @overload
    def __init__(
        self,
        title: str,
        *,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None: ...

    # Core overload — inline positional children.
    @overload
    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None: ...

    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None:
        self.title = title
        self._value: str | MISSING_TYPE = value
        self.icon = icon
        super().__init__(*args)

    @property
    def value(self) -> str:
        if isinstance(self._value, MISSING_TYPE):
            return self.title
        return self._value

    def tagify(self) -> Tag:
        # shiny.ui.accordion does isinstance(panel, AccordionPanel) and
        # rejects pre-rendered Tags, so for standalone .tagify() we stamp
        # a placeholder _accordion_id keyed off the panel's value. The
        # parent :class:`accordion` builds its own AccordionPanel wrappers
        # from this instance's attributes (it can't reuse the rendered
        # Tag).
        import shiny.ui as _sui

        panel = _sui.accordion_panel(
            self.title,
            *self.children,
            value=self._value,
            icon=self.icon,
        )
        panel._accordion_id = f"_orphan_{self.value}"
        return panel.tagify()
```

- [ ] **Step 7.4: Re-export from `__init__.py`**

Modify `pkg-py/src/shinyuiclassonly/__init__.py` — add the import and entry. Final state:

```python
"""shinyuiclassonly — class-per-component UI hierarchy, stripped of session machinery.

(docstring unchanged — see Task 6 step 6.4)
"""

from ._accordion_panel import accordion_panel
from ._base import UiComponent
from ._card import card
from ._children import AllowsChildren
from ._ctx_tag import CtxTag
from ._roles import UiInput, UiLayout, UiOutput

__all__ = [
    "AllowsChildren",
    "CtxTag",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "accordion_panel",
    "card",
]
```

- [ ] **Step 7.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_accordion_panel.py -v`
Expected: PASS (5 tests).

- [ ] **Step 7.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_accordion_panel.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_accordion_panel.py
git commit -m "feat(shinyuiclassonly): accordion_panel layout"
```

---

### Task 8: `accordion`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_accordion.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_accordion.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 8.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_accordion.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui


def test_accordion_tagify_with_panels():
    a = sui.accordion(
        sui.accordion_panel("A", "body a"),
        sui.accordion_panel("B", "body b"),
        id="acc",
    )
    rendered = a.tagify()
    html = str(rendered)
    assert "acc" in html


def test_accordion_with_block_collects_panels():
    import sys

    with sui.accordion(id="acc") as a:
        sys.displayhook(sui.accordion_panel("Settings", "x"))
    assert len(a.children) == 1
    assert isinstance(a.children[0], sui.accordion_panel)


def test_accordion_has_no_open_panels_or_update_methods():
    a = sui.accordion(sui.accordion_panel("A"), id="acc")
    assert not hasattr(a, "open_panels")
    assert not hasattr(a, "update")


def test_accordion_id_required_for_input_routing():
    """The id is still useful (shiny's accordion binding uses it). The
    spec leaves it required to match shinyui."""
    # accordion still constructs without explicit id — it just won't have
    # a server-readable input wire. We allow id to be None to match the
    # spec's "id optional on layouts" intent for shinyuiclassonly.
    sui.accordion(sui.accordion_panel("A"))  # must not raise


def test_accordion_tagify_inline_rebuilds_panels():
    """accordion.tagify() rebuilds shiny.ui.accordion_panel wrappers from
    each child's stored state (because shiny.ui.accordion does an
    isinstance(panel, AccordionPanel) check). Same quirk as shinyui."""
    a = sui.accordion(
        sui.accordion_panel("A", "body"),
        id="acc",
        open="A",
    )
    html = str(a.tagify())
    assert "body" in html
```

- [ ] **Step 8.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_accordion.py -v`
Expected: FAIL.

- [ ] **Step 8.3: Implement `_accordion.py`**

Write `pkg-py/src/shinyuiclassonly/_accordion.py`:

```python
"""accordion — layout with collapsible panels.

Structure-only sibling of ``shinyui.accordion``. Same Express + Core
overloads, same ``tagify()`` strategy (rebuild ``shiny.ui.accordion_panel``
wrappers inline because ``shiny.ui.accordion`` does an
``isinstance(panel, AccordionPanel)`` check on its positional args).
``open_panels()`` and ``update()`` are dropped.
"""

from __future__ import annotations

from typing import Optional, overload

from htmltools import Tag

from ._accordion_panel import accordion_panel
from ._children import AllowsChildren
from ._roles import UiLayout


class accordion(UiLayout, AllowsChildren):
    """Accordion container with collapsible panels.

    No server-side accessor here. Read the open-panel list via
    ``input.<id>()`` and push updates via ``shiny.ui.update_accordion``
    / ``shiny.ui.update_accordion_panel``.
    """

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
    @overload
    def __init__(
        self,
        *,
        id: Optional[str] = None,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None: ...

    # Core overload — inline positional :class:`accordion_panel` instances.
    @overload
    def __init__(
        self,
        *args: accordion_panel,
        id: Optional[str] = None,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None: ...

    def __init__(
        self,
        *args: accordion_panel,
        id: Optional[str] = None,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None:
        self.id = id
        self._open = open
        self.multiple = multiple
        self.class_ = class_
        self.width = width
        self.height = height
        super().__init__(*args)

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        # shiny.ui.accordion rejects pre-rendered Tags (isinstance check on
        # AccordionPanel). Rebuild wrappers from each child's stored state.
        panels = [
            _sui.accordion_panel(
                child.title,  # type: ignore[union-attr]
                *child.children,  # type: ignore[union-attr]
                value=child._value,  # type: ignore[union-attr]
                icon=child.icon,  # type: ignore[union-attr]
            )
            for child in self.children
        ]
        return _sui.accordion(
            *panels,
            id=self.id,
            open=self._open,
            multiple=self.multiple,
            class_=self.class_,
            width=self.width,
            height=self.height,
        ).tagify()
```

- [ ] **Step 8.4: Re-export from `__init__.py`**

Add to `pkg-py/src/shinyuiclassonly/__init__.py`:

```python
from ._accordion import accordion
```

Append `"accordion"` to `__all__`. Final `__all__` after this task:

```python
__all__ = [
    "AllowsChildren",
    "CtxTag",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "accordion",
    "accordion_panel",
    "card",
]
```

- [ ] **Step 8.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_accordion.py -v`
Expected: PASS (5 tests).

- [ ] **Step 8.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_accordion.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_accordion.py
git commit -m "feat(shinyuiclassonly): accordion layout"
```

---

### Task 9: `input_slider`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_input_slider.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_input_slider.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 9.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_input_slider.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui


def test_input_slider_tagify_basic():
    s = sui.input_slider("n", "N", 1, 10, 5)
    html = str(s.tagify())
    assert 'id="n"' in html


def test_input_slider_stores_kwargs():
    s = sui.input_slider("n", "N", 0, 100, 50, step=5, ticks=True)
    assert s.id == "n"
    assert s.label == "N"
    assert s.min == 0
    assert s.max == 100
    assert s._init_value == 50
    assert s.step == 5
    assert s.ticks is True


def test_input_slider_has_no_value_or_update_methods():
    s = sui.input_slider("n", "N", 1, 10, 5)
    assert not hasattr(s, "value")
    assert not hasattr(s, "update")


def test_input_slider_is_uiinput():
    s = sui.input_slider("n", "N", 1, 10, 5)
    assert isinstance(s, sui.UiInput)
    assert isinstance(s, sui.UiComponent)
    assert not isinstance(s, sui.AllowsChildren)
```

- [ ] **Step 9.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_input_slider.py -v`
Expected: FAIL.

- [ ] **Step 9.3: Implement `_input_slider.py`**

Write `pkg-py/src/shinyuiclassonly/_input_slider.py`:

```python
"""input_slider — class-based numeric slider, structure-only.

Structure-only sibling of ``shinyui.input_slider``. Same ``tagify()``
delegation to ``shiny.ui.input_slider``. The ``value()`` accessor and
``update()`` method are dropped — read via ``input.<id>()`` and push
via ``shiny.ui.update_slider`` from the server.
"""

from __future__ import annotations

from typing import Any

from htmltools import Tag

from ._roles import UiInput


class input_slider(UiInput):
    """Numeric slider input."""

    def __init__(
        self,
        id: str,
        label: str,
        min: float,
        max: float,
        value: float | tuple[float, float],
        *,
        step: float | None = None,
        ticks: bool = False,
        animate: bool | Any = False,
        width: str | None = None,
        sep: str = ",",
        pre: str | None = None,
        post: str | None = None,
        time_format: str | None = None,
        timezone: str | None = None,
        drag_range: bool = True,
    ) -> None:
        self.id = id
        self.label = label
        self.min = min
        self.max = max
        self._init_value = value
        self.step = step
        self.ticks = ticks
        self.animate = animate
        self.width = width
        self.sep = sep
        self.pre = pre
        self.post = post
        self.time_format = time_format
        self.timezone = timezone
        self.drag_range = drag_range

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.input_slider(
            self.id,
            self.label,
            self.min,
            self.max,
            self._init_value,
            step=self.step,
            ticks=self.ticks,
            animate=self.animate,
            width=self.width,
            sep=self.sep,
            pre=self.pre,
            post=self.post,
            time_format=self.time_format,
            timezone=self.timezone,
            drag_range=self.drag_range,
        )
```

- [ ] **Step 9.4: Re-export from `__init__.py`**

Add `from ._input_slider import input_slider` and `"input_slider"` to `__all__`.

- [ ] **Step 9.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_input_slider.py -v`
Expected: PASS (4 tests).

- [ ] **Step 9.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_input_slider.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_input_slider.py
git commit -m "feat(shinyuiclassonly): input_slider"
```

---

### Task 10: `input_select`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_input_select.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_input_select.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 10.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_input_select.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui


def test_input_select_tagify_basic():
    s = sui.input_select("c", "Col", {"a": "Alpha", "b": "Beta"})
    html = str(s.tagify())
    assert 'id="c"' in html
    assert "Alpha" in html


def test_input_select_stores_kwargs():
    s = sui.input_select("c", "Col", ["a", "b"], selected="b", multiple=True)
    assert s.id == "c"
    assert s.label == "Col"
    assert s.choices == ["a", "b"]
    assert s._init_selected == "b"
    assert s.multiple is True


def test_input_select_has_no_value_or_update_methods():
    s = sui.input_select("c", "Col", {"a": "A"})
    assert not hasattr(s, "value")
    assert not hasattr(s, "update")


def test_input_select_is_uiinput():
    s = sui.input_select("c", "Col", {"a": "A"})
    assert isinstance(s, sui.UiInput)
```

- [ ] **Step 10.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_input_select.py -v`
Expected: FAIL.

- [ ] **Step 10.3: Implement `_input_select.py`**

Write `pkg-py/src/shinyuiclassonly/_input_select.py`:

```python
"""input_select — class-based dropdown / multi-select, structure-only."""

from __future__ import annotations

from typing import Mapping, Optional, Union

from htmltools import Tag, TagChild

from ._roles import UiInput

_Choices = Mapping[str, str]
_OptGrpChoices = Mapping[str, _Choices]
SelectChoicesArg = Union[
    "list[str]",
    "tuple[str, ...]",
    _Choices,
    _OptGrpChoices,
]


class input_select(UiInput):
    """Dropdown / multi-select input."""

    def __init__(
        self,
        id: str,
        label: TagChild,
        choices: SelectChoicesArg,
        *,
        selected: Optional[str | list[str]] = None,
        multiple: bool = False,
        width: Optional[str] = None,
        size: Optional[str] = None,
    ) -> None:
        self.id = id
        self.label = label
        self.choices = choices
        self._init_selected = selected
        self.multiple = multiple
        self.width = width
        self.size = size

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.input_select(
            self.id,
            self.label,
            self.choices,
            selected=self._init_selected,
            multiple=self.multiple,
            width=self.width,
            size=self.size,
        )
```

- [ ] **Step 10.4: Re-export from `__init__.py`**

Add `from ._input_select import input_select` and `"input_select"` to `__all__`.

- [ ] **Step 10.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_input_select.py -v`
Expected: PASS (4 tests).

- [ ] **Step 10.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_input_select.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_input_select.py
git commit -m "feat(shinyuiclassonly): input_select"
```

---

### Task 11: `input_action_button`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_input_action_button.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_input_action_button.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 11.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_input_action_button.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui


def test_input_action_button_tagify_basic():
    b = sui.input_action_button("go", "Run")
    html = str(b.tagify())
    assert 'id="go"' in html
    assert "Run" in html


def test_input_action_button_stores_kwargs():
    b = sui.input_action_button("go", "Run", width="120px", disabled=True)
    assert b.id == "go"
    assert b.label == "Run"
    assert b.width == "120px"
    assert b.disabled is True


def test_input_action_button_has_no_value_or_update_methods():
    b = sui.input_action_button("go", "Run")
    assert not hasattr(b, "value")
    assert not hasattr(b, "update")


def test_input_action_button_does_not_register_input_handler():
    """shinyuiclassonly drops the __init_subclass__ handler registration.
    Importing input_action_button must NOT register
    ``shinyui.action`` (or any) into shiny's input_handlers registry."""
    from shiny.input_handler import input_handlers

    # Even if a parallel test of shinyui has already registered
    # 'shinyui.action', shinyuiclassonly itself must not add
    # 'shinyuiclassonly.action' or anything similar.
    registered = set(input_handlers._handlers.keys())
    # Importing shinyuiclassonly must not introduce its own handler keys.
    import shinyuiclassonly  # noqa: F401

    assert {k for k in input_handlers._handlers.keys() if "shinyuiclassonly" in k} == set()
    # Sanity: registered set is at least as large as before (no removals).
    assert registered.issubset(input_handlers._handlers.keys())


def test_input_action_button_is_uiinput():
    b = sui.input_action_button("go", "Run")
    assert isinstance(b, sui.UiInput)
```

- [ ] **Step 11.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_input_action_button.py -v`
Expected: FAIL.

- [ ] **Step 11.3: Implement `_input_action_button.py`**

Write `pkg-py/src/shinyuiclassonly/_input_action_button.py`:

```python
"""input_action_button — class-based action button, structure-only.

Structure-only sibling of ``shinyui.input_action_button``. The class-level
``input_handler_name`` and ``__init_subclass__`` registration are dropped
along with all of ``HasInputValue`` (see the spec). Server code reads the
click counter via ``input.<id>()`` directly.
"""

from __future__ import annotations

from typing import Optional

from htmltools import Tag, TagChild

from ._roles import UiInput


class input_action_button(UiInput):
    """Server-readable action button.

    Wire id: ``input.<id>()`` is an integer click counter starting at 0,
    incremented on each click. There is no class-side accessor.
    """

    def __init__(
        self,
        id: str,
        label: TagChild,
        *,
        icon: TagChild = None,
        width: Optional[str] = None,
        disabled: bool = False,
    ) -> None:
        self.id = id
        self.label = label
        self.icon = icon
        self.width = width
        self.disabled = disabled

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.input_action_button(
            self.id,
            self.label,
            icon=self.icon,
            width=self.width,
            disabled=self.disabled,
        )
```

- [ ] **Step 11.4: Re-export from `__init__.py`**

Add `from ._input_action_button import input_action_button` and `"input_action_button"` to `__all__`.

- [ ] **Step 11.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_input_action_button.py -v`
Expected: PASS (5 tests).

- [ ] **Step 11.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_input_action_button.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_input_action_button.py
git commit -m "feat(shinyuiclassonly): input_action_button"
```

---

### Task 12: `output_code`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_output_code.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_output_code.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 12.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_output_code.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui


def test_output_code_tagify_basic():
    o = sui.output_code("summary")
    html = str(o.tagify())
    assert 'id="summary"' in html


def test_output_code_default_placeholder():
    o = sui.output_code("summary")
    assert o.placeholder is True


def test_output_code_placeholder_false():
    o = sui.output_code("summary", placeholder=False)
    assert o.placeholder is False


def test_output_code_is_uioutput():
    o = sui.output_code("summary")
    assert isinstance(o, sui.UiOutput)
    assert not isinstance(o, sui.UiInput)
```

- [ ] **Step 12.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_output_code.py -v`
Expected: FAIL.

- [ ] **Step 12.3: Implement `_output_code.py`**

Write `pkg-py/src/shinyuiclassonly/_output_code.py`:

```python
"""output_code — class-based verbatim-text output, structure-only."""

from __future__ import annotations

from htmltools import Tag

from ._roles import UiOutput


class output_code(UiOutput):
    """Verbatim-text output placeholder.

    No wire input value — pure output. The server populates it by
    decorating a function with ``@render.code`` whose name matches ``id``.
    """

    def __init__(self, id: str, *, placeholder: bool = True) -> None:
        self.id = id
        self.placeholder = placeholder

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.output_code(self.id, placeholder=self.placeholder)
```

- [ ] **Step 12.4: Re-export from `__init__.py`**

Add `from ._output_code import output_code` and `"output_code"` to `__all__`.

- [ ] **Step 12.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_output_code.py -v`
Expected: PASS (4 tests).

- [ ] **Step 12.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_output_code.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_output_code.py
git commit -m "feat(shinyuiclassonly): output_code"
```

---

### Task 13: `output_plot`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_output_plot.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_output_plot.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 13.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_output_plot.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui


def test_output_plot_tagify_basic():
    o = sui.output_plot("plot")
    html = str(o.tagify())
    assert 'id="plot"' in html


def test_output_plot_carries_interaction_flags():
    o = sui.output_plot("plot", click=True, brush=True, dblclick=True, hover=True)
    assert o.click_enabled is True
    assert o.brush_enabled is True
    assert o.dblclick_enabled is True
    assert o.hover_enabled is True


def test_output_plot_no_click_value_accessor():
    o = sui.output_plot("plot", click=True)
    assert not hasattr(o, "click_value")
    assert not hasattr(o, "brush_value")
    assert not hasattr(o, "hover_value")
    assert not hasattr(o, "dbl_value")


def test_output_plot_is_uioutput():
    o = sui.output_plot("plot")
    assert isinstance(o, sui.UiOutput)
```

- [ ] **Step 13.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_output_plot.py -v`
Expected: FAIL.

- [ ] **Step 13.3: Implement `_output_plot.py`**

Write `pkg-py/src/shinyuiclassonly/_output_plot.py`:

```python
"""output_plot — placement helper for plot outputs, structure-only.

Carries the configuration flags (``click``, ``dblclick``, ``hover``,
``brush``, ``inline``, ``fill``). The derived-input accessors that lived
on ``shinyui.render_plot`` are dropped — server code reads
``input.<id>_click()`` / ``input.<id>_brush()`` etc. directly.
"""

from __future__ import annotations

from htmltools import Tag
from shiny.types import MISSING, MISSING_TYPE

from ._roles import UiOutput


class output_plot(UiOutput):
    """Plot output placeholder."""

    def __init__(
        self,
        id: str,
        *,
        width: str | float | int = "100%",
        height: str | float | int = "400px",
        inline: bool = False,
        click: bool = False,
        dblclick: bool = False,
        hover: bool = False,
        brush: bool = False,
        fill: bool | MISSING_TYPE = MISSING,
    ) -> None:
        self.id = id
        self.width = width
        self.height = height
        self.inline = inline
        self.click_enabled = click
        self.dblclick_enabled = dblclick
        self.hover_enabled = hover
        self.brush_enabled = brush
        self.fill = fill

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.output_plot(
            self.id,
            self.width,
            self.height,
            inline=self.inline,
            click=self.click_enabled,
            dblclick=self.dblclick_enabled,
            hover=self.hover_enabled,
            brush=self.brush_enabled,
            fill=self.fill,
        )
```

- [ ] **Step 13.4: Re-export from `__init__.py`**

Add `from ._output_plot import output_plot` and `"output_plot"` to `__all__`.

- [ ] **Step 13.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_output_plot.py -v`
Expected: PASS (4 tests).

- [ ] **Step 13.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_output_plot.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_output_plot.py
git commit -m "feat(shinyuiclassonly): output_plot"
```

---

### Task 14: `render_plot`

**Files:**
- Create: `pkg-py/src/shinyuiclassonly/_render_plot.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_render_plot.py`
- Modify: `pkg-py/src/shinyuiclassonly/__init__.py`

- [ ] **Step 14.1: Write the failing test**

Write `pkg-py/tests/shinyuiclassonly/test_render_plot.py`:

```python
from __future__ import annotations

import shinyuiclassonly as sui


def test_render_plot_extends_shiny_render_plot():
    from shiny.render._render import plot as _shiny_plot

    assert issubclass(sui.render_plot, _shiny_plot)


def test_render_plot_carries_flags():
    @sui.render_plot(click=True, brush=True)
    def _plot():
        return None

    assert _plot.click_enabled is True
    assert _plot.brush_enabled is True
    assert _plot.dblclick_enabled is False
    assert _plot.hover_enabled is False


def test_render_plot_auto_output_ui_returns_output_plot_instance():
    """auto_output_ui must return a shinyuiclassonly.output_plot instance
    (Tagifiable), NOT a tagified Tag."""

    @sui.render_plot(click=True, brush=True)
    def _plot():
        return None

    _plot.output_id = "plot"  # shiny.render.plot sets this via metadata; emulate
    placeholder = _plot.auto_output_ui()
    assert isinstance(placeholder, sui.output_plot)
    assert placeholder.click_enabled is True
    assert placeholder.brush_enabled is True


def test_render_plot_has_no_session_accessors():
    @sui.render_plot()
    def _plot():
        return None

    assert not hasattr(_plot, "click_value")
    assert not hasattr(_plot, "brush_value")
    assert not hasattr(_plot, "dbl_value")
    assert not hasattr(_plot, "hover_value")
```

- [ ] **Step 14.2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_render_plot.py -v`
Expected: FAIL.

- [ ] **Step 14.3: Implement `_render_plot.py`**

Write `pkg-py/src/shinyuiclassonly/_render_plot.py`:

```python
"""render_plot — shiny.render.plot subclass carrying interaction flags.

Structure-only sibling of ``shinyui.render_plot``. Keeps:

  - the interaction flags (``click``, ``dblclick``, ``hover``, ``brush``,
    ``inline``, ``fill``) carried on the renderer
  - the ``auto_output_ui()`` override that emits a
    :class:`shinyuiclassonly.output_plot` so Express's auto-placement
    produces a properly-configured placeholder

Drops the session-bound ``.click_value()`` / ``.dbl_value()`` /
``.hover_value()`` / ``.brush_value()`` accessors — read
``input.<id>_click()`` / ``input.<id>_brush()`` etc. directly from the
server.

Note: ``auto_output_ui()`` returns the ``output_plot`` instance directly
(not ``.tagify()``'d). htmltools' walker tagifies it later. This
reinforces the "components are Tagifiable, not Tag" lesson — and differs
from ``shinyui.render_plot``, which returns a Tag because its
``auto_output_ui`` is typed ``-> Tag``.
"""

from __future__ import annotations

from typing import Any, Optional

from shiny.render._render import plot as _shiny_plot
from shiny.types import MISSING, MISSING_TYPE


class render_plot(_shiny_plot):
    """Plot renderer that auto-places a :class:`output_plot` placeholder."""

    def __init__(
        self,
        _fn: Any = None,
        *,
        alt: Optional[str] = None,
        width: float | None | MISSING_TYPE = MISSING,
        height: float | None | MISSING_TYPE = MISSING,
        inline: bool = False,
        click: bool = False,
        dblclick: bool = False,
        hover: bool = False,
        brush: bool = False,
        fill: bool | MISSING_TYPE = MISSING,
        **kwargs: object,
    ) -> None:
        super().__init__(_fn, alt=alt, width=width, height=height, **kwargs)
        self.inline = inline
        self.click_enabled = click
        self.dblclick_enabled = dblclick
        self.hover_enabled = hover
        self.brush_enabled = brush
        self.fill = fill

    def auto_output_ui(self, **_kw: object):  # type: ignore[override]
        from ._output_plot import output_plot

        return output_plot(
            self.output_id,
            inline=self.inline,
            click=self.click_enabled,
            dblclick=self.dblclick_enabled,
            hover=self.hover_enabled,
            brush=self.brush_enabled,
            fill=self.fill,
        )
```

- [ ] **Step 14.4: Re-export from `__init__.py`**

Add `from ._render_plot import render_plot` and `"render_plot"` to `__all__`. Final `__init__.py` should match the spec's "Public API" listing.

After this task, the full `__init__.py` is:

```python
"""shinyuiclassonly — class-per-component UI hierarchy, stripped of session machinery.

A smaller delta from existing shiny.ui behavior than shinyui: the class
hierarchy, AllowsChildren + parent-tag context stack, and Core/Express
overloads, with no session capture, no `.value()`/`.update()` accessors,
no input-handler or bookmark registration. Server code reads inputs via
`input.<id>()` and pushes updates via `shiny.ui.update_*` the usual way.

See docs/superpowers/specs/2026-05-19-shinyuiclassonly-design.md.
"""

from ._accordion import accordion
from ._accordion_panel import accordion_panel
from ._base import UiComponent
from ._card import card
from ._children import AllowsChildren
from ._ctx_tag import CtxTag
from ._input_action_button import input_action_button
from ._input_select import input_select
from ._input_slider import input_slider
from ._output_code import output_code
from ._output_plot import output_plot
from ._render_plot import render_plot
from ._roles import UiInput, UiLayout, UiOutput

__all__ = [
    "AllowsChildren",
    "CtxTag",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "accordion",
    "accordion_panel",
    "card",
    "input_action_button",
    "input_select",
    "input_slider",
    "output_code",
    "output_plot",
    "render_plot",
]
```

- [ ] **Step 14.5: Run tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/test_render_plot.py -v`
Expected: PASS (4 tests).

- [ ] **Step 14.6: Commit**

```bash
git add pkg-py/src/shinyuiclassonly/_render_plot.py \
        pkg-py/src/shinyuiclassonly/__init__.py \
        pkg-py/tests/shinyuiclassonly/test_render_plot.py
git commit -m "feat(shinyuiclassonly): render_plot with auto_output_ui returning output_plot"
```

---

### Task 15: Hierarchy, public-exports, smoke tests

**Files:**
- Create: `pkg-py/tests/shinyuiclassonly/test_hierarchy.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_public_exports.py`
- Create: `pkg-py/tests/shinyuiclassonly/test_smoke.py`

- [ ] **Step 15.1: Write `test_hierarchy.py`**

Write `pkg-py/tests/shinyuiclassonly/test_hierarchy.py`:

```python
"""Cross-class hierarchy assertions.

Mirrors the spirit of pkg-py/tests/shinyui/test_hierarchy.py but with the
session-related bases dropped from expected_bases.
"""

from __future__ import annotations

import pytest
import shinyuiclassonly as sui


def _maker(cls):
    if cls is sui.input_slider:
        return sui.input_slider("n", "N", 1, 10, 5)
    if cls is sui.input_select:
        return sui.input_select("c", "C", {"a": "A"})
    if cls is sui.input_action_button:
        return sui.input_action_button("go", "Run")
    if cls is sui.output_code:
        return sui.output_code("o")
    if cls is sui.output_plot:
        return sui.output_plot("p")
    if cls is sui.card:
        return sui.card("b", id="m")
    if cls is sui.accordion:
        return sui.accordion(sui.accordion_panel("A"), id="acc")
    if cls is sui.accordion_panel:
        return sui.accordion_panel("X", "y")
    raise AssertionError(f"no maker for {cls}")


ALL_CLASSES = [
    sui.input_slider,
    sui.input_select,
    sui.input_action_button,
    sui.output_code,
    sui.output_plot,
    sui.card,
    sui.accordion,
    sui.accordion_panel,
]


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_is_uicomponent(cls):
    assert isinstance(_maker(cls), sui.UiComponent)


@pytest.mark.parametrize(
    "cls,expected",
    [
        (sui.input_slider, {sui.UiInput}),
        (sui.input_select, {sui.UiInput}),
        (sui.input_action_button, {sui.UiInput}),
        (sui.output_code, {sui.UiOutput}),
        (sui.output_plot, {sui.UiOutput}),
        (sui.card, {sui.UiLayout, sui.AllowsChildren}),
        (sui.accordion, {sui.UiLayout, sui.AllowsChildren}),
        (sui.accordion_panel, {sui.UiLayout, sui.AllowsChildren}),
    ],
)
def test_expected_bases(cls, expected):
    inst = _maker(cls)
    for base in expected:
        assert isinstance(inst, base), (
            f"{cls.__name__} should be instance of {base.__name__}"
        )


@pytest.mark.parametrize(
    "cls,allows_children",
    [
        (sui.input_slider, False),
        (sui.input_select, False),
        (sui.input_action_button, False),
        (sui.output_code, False),
        (sui.output_plot, False),
        (sui.card, True),
        (sui.accordion, True),
        (sui.accordion_panel, True),
    ],
)
def test_with_block_protocol(cls, allows_children):
    inst = _maker(cls)
    if allows_children:
        with inst as ctx:
            assert ctx is inst
    else:
        with pytest.raises(TypeError, match=r"context manager protocol"):
            with inst:  # noqa: B017
                pass
```

- [ ] **Step 15.2: Write `test_public_exports.py`**

Write `pkg-py/tests/shinyuiclassonly/test_public_exports.py`:

```python
"""Assert __all__ matches what we export and the dropped symbols stay dropped."""

from __future__ import annotations

import shinyuiclassonly as sui


EXPECTED = {
    "AllowsChildren",
    "CtxTag",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "accordion",
    "accordion_panel",
    "card",
    "input_action_button",
    "input_select",
    "input_slider",
    "output_code",
    "output_plot",
    "render_plot",
}


def test_all_matches_expected():
    assert set(sui.__all__) == EXPECTED


def test_each_name_is_actually_exported():
    for name in sui.__all__:
        assert hasattr(sui, name), f"{name} listed in __all__ but not exported"


def test_dropped_shinyui_symbols_are_not_exported():
    """Symbols intentionally dropped from shinyuiclassonly relative to shinyui."""
    for name in ("HasInputValue", "Updatable", "lookup_component"):
        assert not hasattr(sui, name), f"{name} should not exist on shinyuiclassonly"
```

- [ ] **Step 15.3: Write `test_smoke.py`**

Write `pkg-py/tests/shinyuiclassonly/test_smoke.py`:

```python
"""End-to-end smoke: build a UI tree and tagify it without errors."""

from __future__ import annotations

import shinyuiclassonly as sui
from shiny import ui as _sui


def test_full_tree_tagifies():
    tree = _sui.page_fluid(
        sui.card(
            sui.accordion(
                sui.accordion_panel(
                    "Settings",
                    sui.input_slider("n", "N", 1, 10, 5),
                    sui.input_select("c", "Col", {"a": "A"}),
                    sui.input_action_button("go", "Run"),
                ),
                sui.accordion_panel(
                    "Diagnostics",
                    sui.output_code("summary"),
                    sui.output_plot("plot", click=True, brush=True),
                ),
                id="acc",
                open="Settings",
            ),
            id="m",
            full_screen=False,
        ),
        title="smoke",
    )
    html = str(tree.tagify())
    # Verify a handful of pieces ended up in the rendered HTML.
    assert 'id="n"' in html
    assert 'id="c"' in html
    assert 'id="go"' in html
    assert 'id="summary"' in html
    assert 'id="plot"' in html
    assert "Settings" in html
    assert "Diagnostics" in html
```

- [ ] **Step 15.4: Run the cross-class tests**

Run: `uv run pytest pkg-py/tests/shinyuiclassonly/ -v`
Expected: PASS (every test in the suite, ~50+).

- [ ] **Step 15.5: Run the full Python check (formatting, types, tests)**

Run: `make py-check`
Expected: PASS. If pyright complains, fix the offending annotation; if ruff complains, fix the formatting (no manual `# noqa` unless required for the same reason `shinyui` already has it).

- [ ] **Step 15.6: Commit**

```bash
git add pkg-py/tests/shinyuiclassonly/test_hierarchy.py \
        pkg-py/tests/shinyuiclassonly/test_public_exports.py \
        pkg-py/tests/shinyuiclassonly/test_smoke.py
git commit -m "test(shinyuiclassonly): cross-class hierarchy, exports, smoke"
```

---

### Task 16: Example 16 — Core (positional) form

**Files:**
- Create: `examples/app-py/16-shinyuiclassonly-core/app.py`

- [ ] **Step 16.1: Write the example app**

Write `examples/app-py/16-shinyuiclassonly-core/app.py`:

```python
"""End-to-end demo of shinyuiclassonly's class hierarchy in **Shiny Core**.

This is the Core (positional composition) variant. Its sibling
``17-shinyuiclassonly-express/app.py`` builds the same UI tree in Shiny
Express using ``with``-blocks.

Compared with examples 14 / 15 (the ``shinyui`` versions of this app):

  - The same component classes (``card``, ``accordion``,
    ``accordion_panel``, ``input_slider``, …) are imported, but from
    ``shinyuiclassonly`` instead of ``shinyui``.
  - No walrus operators on inputs or layouts. The server reads inputs via
    ``input.<id>()`` directly, so there is no reason to bind a
    module-level name on any component instance.
  - Reads use ``input.<id>()`` instead of ``n_slider.value()`` /
    ``acc.open_panels()`` / ``main_card.full_screen_value()`` /
    ``plot.click_value()``.
  - Updates use ``shiny.ui.update_accordion(...)`` directly instead of
    ``acc.update(...)``.
  - The plot renderer (``shinyuiclassonly.render_plot``) still carries
    the interaction flags and auto-places its ``output_plot``; it just
    no longer carries ``.click_value`` / ``.brush_value`` accessors.

The architectural delta between this file and example 14 is the cost of
the session-bound machinery that ``shinyui`` adds on top of the class
hierarchy.
"""

from __future__ import annotations

import shinyuiclassonly as su
from shiny import App, Inputs, Outputs, Session, reactive, render
from shiny import ui as _sui

# --- UI ---------------------------------------------------------------------
app_ui = _sui.page_fluid(
    su.card(
        _sui.layout_column_wrap(
            su.input_action_button("open_all", "Open all panels"),
            su.input_action_button("close_all", "Close all panels"),
            width=1 / 2,
        ),
        su.accordion(
            su.accordion_panel(
                "Settings",
                su.input_slider("n", "Sample size", 10, 1000, 100),
                su.input_select(
                    "dist",
                    "Distribution",
                    {"normal": "Normal", "uniform": "Uniform"},
                ),
                su.input_slider("seed", "Seed", 1, 1000, 42),
            ),
            su.accordion_panel(
                "Diagnostics",
                su.output_code("summary"),
                su.output_code("diag"),
            ),
            id="acc",
            open="Settings",
        ),
        su.output_plot("plot", click=True, brush=True),
        id="main_card",
        full_screen=False,
    ),
    title="shinyuiclassonly — Core (positional) form",
)


# --- Server -----------------------------------------------------------------
def server(input: Inputs, output: Outputs, session: Session) -> None:
    @render.code
    def summary() -> str:
        return (
            f"n     = {input.n()}\n"
            f"dist  = {input.dist()}\n"
            f"seed  = {input.seed()}\n"
            f"open  = {tuple(input.acc() or ())}\n"
            f"fs    = {bool(input.main_card_full_screen())}\n"
        )

    @render.code
    def diag() -> str:
        return (
            f"click = {input.plot_click()}\n"
            f"brush = {input.plot_brush()}\n"
        )

    @su.render_plot(click=True, brush=True)
    def plot():
        import matplotlib.pyplot as plt
        import numpy as np

        rng = np.random.default_rng(input.seed())
        n = input.n()
        if input.dist() == "normal":
            x = rng.standard_normal(n)
            y = rng.standard_normal(n)
        else:
            x = rng.uniform(-2, 2, n)
            y = rng.uniform(-2, 2, n)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(x, y, s=12, alpha=0.6)
        ax.set_title(f"{input.dist()} sample, n={n}, seed={input.seed()}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, alpha=0.3)
        return fig

    @reactive.effect
    @reactive.event(input.open_all, ignore_init=True)
    def _open_all_panels():
        _sui.update_accordion("acc", show=["Settings", "Diagnostics"], session=session)

    @reactive.effect
    @reactive.event(input.close_all, ignore_init=True)
    def _close_all_panels():
        _sui.update_accordion("acc", show=False, session=session)


app = App(app_ui, server)
```

- [ ] **Step 16.2: Sanity-check the example imports and constructs `app_ui`**

Run: `uv run python -c "import sys; sys.path.insert(0, 'examples/app-py/16-shinyuiclassonly-core'); import app; print(type(app.app_ui).__name__)"`
Expected: `Tag` (or `TagList` — either is fine; the point is that no exception fires).

- [ ] **Step 16.3: Commit**

```bash
git add examples/app-py/16-shinyuiclassonly-core/app.py
git commit -m "examples: 16-shinyuiclassonly-core (positional / Core form)"
```

---

### Task 17: Example 17 — Express (with-block) form

**Files:**
- Create: `examples/app-py/17-shinyuiclassonly-express/app.py`

- [ ] **Step 17.1: Write the example app**

Write `examples/app-py/17-shinyuiclassonly-express/app.py`:

```python
# End-to-end demo of shinyuiclassonly's class hierarchy in `with` form.
#
# Express variant of `16-shinyuiclassonly-core/`. Both apps produce the same
# UI tree. Compared with example 15 (the ``shinyui`` ``with``-block demo):
#
#   - imports ``shinyuiclassonly as su`` instead of ``shinyui as su``
#   - no walrus operators: the server reads inputs via ``input.<id>()``
#     directly, so there is no reason to bind a module-level name on any
#     component instance.
#   - reads use ``input.<id>()`` instead of ``n_slider.value()`` etc.
#   - updates use ``shiny.ui.update_accordion(...)`` instead of
#     ``acc.update(...)``.
#   - the plot renderer (``shinyuiclassonly.render_plot``) still carries
#     the interaction flags and auto-places its ``output_plot``; it just
#     no longer carries ``.click_value`` / ``.brush_value`` accessors.
#
# Both rely on ``@expressify`` (Shiny Express's default for ``app.py``) so
# bare expression statements get rewritten to ``sys.displayhook(...)``
# calls. The shinyuiclassonly parent-tag context stack routes those values
# to the innermost active ``with`` parent.
#
# A module-level docstring would render as raw text on the page because
# ``@expressify`` wraps every bare-expression statement (including the
# docstring) in ``sys.displayhook(...)``. So this module uses a comment
# block instead.

from __future__ import annotations

import shinyuiclassonly as su
from shiny import reactive, render
from shiny import ui as _sui
from shiny.express import ui

# --- Page ------------------------------------------------------------------
ui.page_opts(title="shinyuiclassonly — Express with-blocks")

ui.markdown(
    """
    ### shinyuiclassonly — Express with-blocks

    Express variant of `16-shinyuiclassonly-core/`. Same components, same
    tree, expressed as `with card(): with accordion(): ...`. The server
    reads inputs via `input.<id>()` directly — no walrus bindings needed.
    """
)

with su.card(id="main_card", full_screen=False):
    _sui.layout_column_wrap(
        su.input_action_button("open_all", "Open all panels"),
        su.input_action_button("close_all", "Close all panels"),
        width=1 / 2,
    )
    with su.accordion(id="acc", open="Settings"):
        with su.accordion_panel("Settings"):
            su.input_slider("n", "Sample size", 10, 1000, 100)
            su.input_select(
                "dist",
                "Distribution",
                {"normal": "Normal", "uniform": "Uniform"},
            )
            su.input_slider("seed", "Seed", 1, 1000, 42)
        with su.accordion_panel("Diagnostics"):

            @render.code
            def summary():
                from shiny.express import input

                return (
                    f"n     = {input.n()}\n"
                    f"dist  = {input.dist()}\n"
                    f"seed  = {input.seed()}\n"
                    f"open  = {tuple(input.acc() or ())}\n"
                    f"fs    = {bool(input.main_card_full_screen())}\n"
                )

            @render.code
            def diag():
                from shiny.express import input

                return (
                    f"click = {input.plot_click()}\n"
                    f"brush = {input.plot_brush()}\n"
                )

    @su.render_plot(click=True, brush=True)
    def plot():
        import matplotlib.pyplot as plt
        import numpy as np
        from shiny.express import input

        rng = np.random.default_rng(input.seed())
        n = input.n()
        if input.dist() == "normal":
            x = rng.standard_normal(n)
            y = rng.standard_normal(n)
        else:
            x = rng.uniform(-2, 2, n)
            y = rng.uniform(-2, 2, n)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(x, y, s=12, alpha=0.6)
        ax.set_title(f"{input.dist()} sample, n={n}, seed={input.seed()}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, alpha=0.3)
        return fig


# --- Reactive effects ------------------------------------------------------
@reactive.effect
@reactive.event(_input := __import__("shiny.express", fromlist=["input"]).input.open_all, ignore_init=True)
def _open_all_panels():
    _sui.update_accordion("acc", show=["Settings", "Diagnostics"])


@reactive.effect
@reactive.event(__import__("shiny.express", fromlist=["input"]).input.close_all, ignore_init=True)
def _close_all_panels():
    _sui.update_accordion("acc", show=False)
```

**Note on `from shiny.express import input`:** in Shiny Express, `input` is exposed via the `shiny.express` module rather than as a function argument. The `from shiny.express import input` line inside each renderer is the idiomatic pattern Express examples already use. The decorator-level `__import__` dance at the bottom is necessary because `@reactive.event` needs the *reactive value*, not a lazy lookup; we pull `input.open_all` and `input.close_all` at decorator-evaluation time.

If a cleaner pattern is already established elsewhere in `examples/app-py/` (e.g. example 15 references `open_all_btn.value` via the walrus binding), you may move the `from shiny.express import input` import to module top and use plain `input.open_all` references at the decorator line.

- [ ] **Step 17.2: Sanity-check the example imports**

Run: `uv run python -c "import sys; sys.path.insert(0, 'examples/app-py/17-shinyuiclassonly-express'); import app"`
Expected: no exception. (Express apps build their UI as a side-effect of import; we don't need to render — just import without error.)

- [ ] **Step 17.3: Commit**

```bash
git add examples/app-py/17-shinyuiclassonly-express/app.py
git commit -m "examples: 17-shinyuiclassonly-express (with-block / Express form)"
```

---

### Task 18: CLAUDE.md updates

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 18.1: Update the "Repo structure" block**

In `CLAUDE.md`, replace the existing `pkg-py/` block in "Repo structure":

Find:
```
pkg-py/                     # Python package
  src/shinyreact/           # Package: set_react_page, reactive_output, page_react, Spec/Element/Node
    www/                    # Bundled JS
  tests/                    # pytest tests
```

Replace with:
```
pkg-py/                     # Python packages (three shipped from one wheel)
  src/shinyreact/           # Core JSON-spec / React-bridge package
    www/                    # Bundled JS
  src/shinyui/              # Class-per-component UI hierarchy prototype (session-aware)
  src/shinyuiclassonly/     # Class-per-component UI hierarchy, structure only (no session)
  tests/                    # pytest tests for all three packages
```

- [ ] **Step 18.2: Insert the "Sibling packages" section**

In `CLAUDE.md`, insert this new section between the existing "Repo structure" and "Commands" sections (i.e. after the closing of the repo-structure code fence and the blank line that follows it, before the `## Commands` heading):

```markdown
## Sibling packages: shinyui and shinyuiclassonly

Two prototype packages explore a class-per-component UI hierarchy as a possible direction for `py-shiny`'s `ui.*` surface. They share the same component vocabulary (`card`, `accordion`, `input_slider`, …) but differ in what server-side machinery comes attached.

- **`shinyui`** — the full prototype. Every component is a `Tagifiable` class that *also* captures the active session at construction, registers itself with a per-session id→instance map, exposes typed reactive accessors (`slider.value()`, `card.full_screen_value()`, `acc.open_panels()`), supports server-driven `update(...)`, owns its input handler and bookmark serializer, and ships a `render_plot` with derived-input accessors (`click_value`, `brush_value`, …). This is what the umbrella design (`docs/superpowers/specs/2026-05-06-unified-ui-component-class-design.md`) proposes for upstream `py-shiny`. Examples 14 and 15 demonstrate it in Core (positional) and Express (`with`-block) form respectively.

- **`shinyuiclassonly`** — the *small delta* the team can compare against today's `ui.*`. Same component classes and same hierarchy (`UiComponent`, `UiInput`, `UiOutput`, `UiLayout`, `AllowsChildren`, parent-tag context stack), but with **none** of the session-bound machinery: no `_session` capture, no `.value()` / `.update()` / `.click_value()` accessors, no input-handler or bookmark registration, no per-session instance registry, no `reactive_calc_method`. Components are pure `Tagifiable` objects. Server code reads inputs via `input.<id>()` and pushes updates via `shiny.ui.update_*` — exactly like today. Examples 16 and 17 mirror 14 and 15 line-for-line so the diff is small enough to read in one sitting.

Use **`shinyuiclassonly`** when motivating "what does the class hierarchy give us, structurally, before we add server-side ergonomics?" — it's the cheapest possible step from `ui.card(...)` → `card(...)`. Use **`shinyui`** when motivating the full vision (typed accessors, `update()` on the instance, auto-placement of renderers).
```

- [ ] **Step 18.3: Verify markdown renders cleanly**

Run: `uv run python -c "from pathlib import Path; t = Path('CLAUDE.md').read_text(); assert '## Sibling packages: shinyui and shinyuiclassonly' in t; assert 'shinyuiclassonly' in t.split('## Repo structure', 1)[1].split('## Commands', 1)[0]; print('ok')"`
Expected output: `ok`

- [ ] **Step 18.4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): document shinyui vs. shinyuiclassonly sibling packages"
```

---

### Task 19: Final verification

- [ ] **Step 19.1: Run the full Python check matrix**

Run: `make py-check`
Expected: PASS — formatting, type-checking, and the full test suite.

- [ ] **Step 19.2: Confirm no `shinyui` import is missing or mistakenly added**

Run: `grep -rn "import shinyui" pkg-py/src/shinyuiclassonly/ || echo OK`
Expected output: `OK` (the new package must not depend on `shinyui`).

Run: `grep -rn "import shinyui" examples/app-py/16-shinyuiclassonly-core/ examples/app-py/17-shinyuiclassonly-express/ || echo OK`
Expected output: `OK` (examples must not import `shinyui`; they import `shinyuiclassonly`).

- [ ] **Step 19.3: Confirm no session-related symbol leaked in**

Run: `grep -rn "_session\|_require_session\|_read_input\|HasInputValue\|Updatable\|reactive_calc_method\|lookup_component" pkg-py/src/shinyuiclassonly/ || echo OK`
Expected output: `OK`.

- [ ] **Step 19.4: Quick visual smoke run (manual)**

Run: `uv run shiny run examples/app-py/16-shinyuiclassonly-core/app.py --port 0` in one terminal, point a browser at the printed URL, exercise the panels, sliders, and the plot's click / brush. Then repeat for `17-shinyuiclassonly-express/app.py`. Both apps must render and react.

If automated UI testing is desired, refer to `.claude/references/playwright-e2e-tests.md` — but the spec does not require Playwright tests for this prototype.

- [ ] **Step 19.5: Final commit (if anything turned up in 19.1–19.3)**

If any of the previous verification steps required fixes, stage and commit:

```bash
git add -A   # only after reviewing what's staged
git commit -m "chore(shinyuiclassonly): final cleanups from verification"
```

If nothing needed fixing, skip this step.

---

## Self-Review

Spec sections vs. plan tasks:

| Spec section                          | Tasks      |
|---------------------------------------|------------|
| Package layout                        | 1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 |
| Build wiring                          | 1          |
| Class hierarchy (UiComponent, roles)  | 2, 3       |
| AllowsChildren mixin                  | 5          |
| Parent-tag stack + CtxTag             | 4          |
| Concrete components (8 classes)       | 6–13       |
| render_plot                           | 14         |
| Public API (`__init__.py` `__all__`)  | 14, 15     |
| Examples 16, 17                       | 16, 17     |
| Tests parallel to shinyui             | 2–15       |
| CLAUDE.md updates                     | 18         |

No placeholder text found. No "TBD" / "implement later" / "similar to Task N" left. Every step shows the actual file contents or shell command that the engineer needs.

Type / API consistency check:

- `UiComponent.tagify(self) -> Tag` declared in Task 2; concrete `tagify()` overrides in Tasks 6–13 return `Tag` via `shiny.ui.*.tagify()`.
- `render_plot.auto_output_ui()` (Task 14) returns `output_plot` instance — consistent with `output_plot` defined in Task 13.
- `card.id`, `accordion.id` are `Optional[str]` — consistent across the test in Task 6 (`test_card_id_optional`) and the implementation in Task 8 (`id: Optional[str] = None`).
- Final `__all__` listing in Task 14 matches `EXPECTED` set in `test_public_exports.py` (Task 15).

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-shinyuiclassonly.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatches a fresh subagent per task, reviews between tasks, fast iteration.

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
