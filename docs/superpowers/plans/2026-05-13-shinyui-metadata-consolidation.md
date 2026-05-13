# shinyui Metadata Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new sibling Python package `shinyui` at `pkg-py/src/shinyui/` that prototypes a class-per-component UI hierarchy with seven concrete archetypes, single source of session truth on `UiComponent`, typed `update()` methods, server-side read accessors, class-owned bookmark serializers, and a working end-to-end example app.

**Architecture:** Three role base classes (`UiInput`/`UiOutput`/`UiLayout`) plus three orthogonal mixins (`HasInputValue`/`Updatable`/`AllowsChildren`). Concrete classes pick the bases they need. Session is captured once at `UiComponent.__init__`; reads, updates, and bookmark registration all funnel through one helper. Markup is copied (not wrapped) from `shiny.ui.*` so `shinyui` has no runtime dependency on shiny's UI factories.

**Tech Stack:** Python 3.10+, `shiny>=1.2.0`, `htmltools>=0.6.0`, `pytest`, `pyright`. No new dependencies.

**Source of truth design spec:** `docs/superpowers/specs/2026-05-13-shinyui-metadata-consolidation-design.md`

---

## File Structure

```
pyproject.toml                       # MODIFY: add shinyui to wheel packages + pyright include

pkg-py/src/shinyui/
  __init__.py                        # CREATE: public exports
  _base.py                           # CREATE: UiComponent (ABC)
  _children.py                       # CREATE: AllowsChildren mixin
  _input_value.py                    # CREATE: HasInputValue mixin
  _updatable.py                      # CREATE: Updatable mixin (ABC)
  _roles.py                          # CREATE: UiInput, UiOutput, UiLayout
  _reactive.py                       # CREATE: reactive_calc_method (~15-line decorator)
  _input_slider.py                   # CREATE: UiInputSlider + input_slider()
  _input_select.py                   # CREATE: UiInputSelect + input_select()
  _output_code.py                    # CREATE: UiOutputCode + output_code()
  _output_plot.py                    # CREATE: UiOutputPlot + output_plot()
  _accordion_panel.py                # CREATE: UiAccordionPanel + accordion_panel()
  _accordion.py                      # CREATE: UiAccordion + accordion()
  _card.py                           # CREATE: UiCard + card()
  _bookmark.py                       # CREATE: id→instance session map + class-owned serializer hook

pkg-py/tests/shinyui/
  __init__.py                        # CREATE: empty
  conftest.py                        # CREATE: shared session_context fixture
  test_base.py                       # CREATE: UiComponent unit tests
  test_children.py                   # CREATE: AllowsChildren unit tests
  test_input_value.py                # CREATE: HasInputValue unit tests
  test_updatable.py                  # CREATE: Updatable unit tests
  test_roles.py                      # CREATE: role-class smoke tests
  test_reactive.py                   # CREATE: reactive_calc_method unit tests
  test_input_slider.py               # CREATE: per-class tests + snapshot
  test_input_select.py               # CREATE: per-class tests + snapshot
  test_output_code.py                # CREATE: per-class tests + snapshot
  test_output_plot.py                # CREATE: per-class tests + snapshot
  test_accordion_panel.py            # CREATE: per-class tests + snapshot
  test_accordion.py                  # CREATE: per-class tests + snapshot
  test_card.py                       # CREATE: per-class tests + snapshot
  test_hierarchy.py                  # CREATE: cross-cutting MRO + isinstance + with-block-raises
  test_input_handler_registration.py # CREATE: registry contents after import
  test_bookmark_roundtrip.py         # CREATE: integration test for save/restore
  test_update_resolution.py          # CREATE: session resolution rules for update()
  test_read_accessors.py             # CREATE: cross-class accessor behavior
  test_allows_children.py            # CREATE: cross-class with-block + append behavior

examples/app-py/14-unified-ui-prototype/
  app.py                             # CREATE: end-to-end demo
  README.md                          # CREATE: walkthrough
```

---

## Task 1: Package scaffolding

**Files:**
- Modify: `pyproject.toml`
- Create: `pkg-py/src/shinyui/__init__.py`
- Create: `pkg-py/tests/shinyui/__init__.py`
- Create: `pkg-py/tests/shinyui/conftest.py`
- Create: `pkg-py/tests/shinyui/test_smoke.py`

- [ ] **Step 1: Read existing pyproject.toml to confirm current shape**

Run: read `pyproject.toml`. Confirm `[tool.hatch.build.targets.wheel] packages = ["pkg-py/src/shinyreact"]` and `[tool.pyright] include = ["pkg-py/src/shinyreact"]` are present.

- [ ] **Step 2: Add shinyui to wheel targets and pyright include**

Edit `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["pkg-py/src/shinyreact", "pkg-py/src/shinyui"]

[tool.pyright]
include = ["pkg-py/src/shinyreact", "pkg-py/src/shinyui"]
pythonVersion = "3.10"
typeCheckingMode = "basic"
```

- [ ] **Step 3: Create the package skeleton**

Create `pkg-py/src/shinyui/__init__.py`:

```python
"""shinyui — prototype class-per-component UI hierarchy.

See docs/superpowers/specs/2026-05-13-shinyui-metadata-consolidation-design.md.
"""

__all__: list[str] = []
```

Create `pkg-py/tests/shinyui/__init__.py` as an empty file.

- [ ] **Step 4: Create shared session fixture**

Create `pkg-py/tests/shinyui/conftest.py`:

```python
"""Shared fixtures for shinyui tests.

Each test that needs `get_current_session()` to return something uses
the `mock_session` fixture, which yields a controllable Session-like object
and binds it as the current session for the duration of the test.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest
from shiny.session._utils import session_context


@pytest.fixture
def mock_session() -> Iterator[Any]:
    """Bind a MagicMock as the current session inside the test body."""
    session = MagicMock(name="MockSession")
    session.input = MagicMock(name="MockInput")
    with session_context(session):
        yield session


@contextmanager
def no_session() -> Iterator[None]:
    """Helper: confirm no session is bound. Use for explicit clarity in tests."""
    from shiny.session import get_current_session
    assert get_current_session() is None, "Test expected no active session"
    yield
```

- [ ] **Step 5: Write a smoke test**

Create `pkg-py/tests/shinyui/test_smoke.py`:

```python
def test_package_importable():
    import shinyui  # noqa: F401


def test_mock_session_fixture(mock_session):
    from shiny.session import get_current_session
    assert get_current_session() is mock_session
```

- [ ] **Step 6: Run the smoke test**

Run: `uv run pytest pkg-py/tests/shinyui/test_smoke.py -v`
Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml pkg-py/src/shinyui pkg-py/tests/shinyui
git commit -m "feat(shinyui): scaffold sibling package + test infra"
```

---

## Task 2: `UiComponent` base class

**Files:**
- Create: `pkg-py/src/shinyui/_base.py`
- Create: `pkg-py/tests/shinyui/test_base.py`

- [ ] **Step 1: Write failing tests for UiComponent**

Create `pkg-py/tests/shinyui/test_base.py`:

```python
from __future__ import annotations

import pytest

from shinyui._base import UiComponent


class _Dummy(UiComponent):
    """Minimal concrete subclass for testing."""
    def tagify(self):
        from htmltools import tags
        return tags.div("dummy")


def test_uicomponent_is_abstract():
    with pytest.raises(TypeError):
        UiComponent()  # type: ignore[abstract]


def test_session_captured_as_none_without_session():
    c = _Dummy()
    assert c._session is None


def test_session_captured_when_present(mock_session):
    c = _Dummy()
    assert c._session is mock_session


def test_require_session_raises_when_none():
    c = _Dummy()
    with pytest.raises(RuntimeError, match=r"_Dummy\.foo\(\) requires an active session"):
        c._require_session(for_op="foo")


def test_require_session_returns_captured(mock_session):
    c = _Dummy()
    assert c._require_session(for_op="foo") is mock_session


def test_require_session_falls_back_to_current(mock_session):
    """If _session is None at init but a session is active at call time, use it."""
    from shiny.session._utils import session_context
    c = _Dummy()                            # no session captured (constructed before fixture binding? — re-bind)
    c._session = None                       # explicitly clear
    with session_context(mock_session):
        assert c._require_session(for_op="foo") is mock_session


def test_enter_raises_with_class_name():
    c = _Dummy()
    with pytest.raises(TypeError, match=r"_Dummy does not accept children"):
        c.__enter__()


def test_read_input_uses_current_session_and_id(mock_session):
    c = _Dummy()
    c.id = "my_id"
    mock_session.input.__getitem__.return_value = lambda: 42
    assert c._read_input() == 42
    mock_session.input.__getitem__.assert_called_with("my_id")


def test_read_input_suffix(mock_session):
    c = _Dummy()
    c.id = "p"
    mock_session.input.__getitem__.return_value = lambda: {"x": 1}
    assert c._read_input("_click") == {"x": 1}
    mock_session.input.__getitem__.assert_called_with("p_click")
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_base.py -v`
Expected: All fail with `ModuleNotFoundError: No module named 'shinyui._base'`.

- [ ] **Step 3: Implement UiComponent**

Create `pkg-py/src/shinyui/_base.py`:

```python
"""UiComponent — abstract base for the shinyui class hierarchy.

Single source of truth for:
  - `self._session`: the active session captured at construction (may be None)
  - `_require_session(for_op=...)`: resolves a session at call time, with a fallback
    to the current session, raising RuntimeError if none is reachable.
  - `_read_input(suffix="")`: reads `session.input[f"{self.id}{suffix}"]()`.

`tagify()` is abstract. `__enter__` raises by default; `AllowsChildren` overrides.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self

from htmltools import HTMLDependency, Tag
from shiny.session import Session, get_current_session


class UiComponent(ABC):
    html_dependencies: ClassVar[tuple[HTMLDependency, ...]] = ()

    def __init__(self, **kwargs: Any) -> None:
        # Capture session BEFORE super() so mixins can read self._session
        # in their own __init__ after they call super().__init__(**kw).
        self._session: Session | None = get_current_session()
        super().__init__(**kwargs)

    def _require_session(self, *, for_op: str) -> Session:
        sess = self._session or get_current_session()
        if sess is None:
            raise RuntimeError(
                f"{type(self).__name__}.{for_op}() requires an active session "
                f"(instance constructed outside any session, and none is active now)"
            )
        return sess

    def _read_input(self, suffix: str = "") -> Any:
        sess = self._require_session(for_op="_read_input")
        return sess.input[f"{self.id}{suffix}"]()  # type: ignore[attr-defined]

    @abstractmethod
    def tagify(self) -> Tag: ...

    def __enter__(self) -> Self:
        raise TypeError(
            f"{type(self).__name__} does not accept children; "
            f"only components declaring `AllowsChildren` may be used as `with` blocks."
        )

    def __exit__(self, *exc: object) -> None:
        return None
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_base.py -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/_base.py pkg-py/tests/shinyui/test_base.py
git commit -m "feat(shinyui): UiComponent base + session/read helpers"
```

---

## Task 3: `AllowsChildren` mixin

**Files:**
- Create: `pkg-py/src/shinyui/_children.py`
- Create: `pkg-py/tests/shinyui/test_children.py`

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_children.py`:

```python
from __future__ import annotations

from htmltools import tags

from shinyui._base import UiComponent
from shinyui._children import AllowsChildren


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


def test_with_block_returns_self_and_collects_via_append():
    with _ChildBox() as b:
        b.append("inside")
    assert b.children == ["inside"]


def test_enter_does_not_raise():
    # Inherits from UiComponent (which raises), but AllowsChildren overrides.
    b = _ChildBox()
    # Should not raise:
    assert b.__enter__() is b
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_children.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement AllowsChildren**

Create `pkg-py/src/shinyui/_children.py`:

```python
"""AllowsChildren — mixin for components that accept children.

Mixin protocol:
  - Subclasses MUST call `super().__init__(**kwargs)` first in their __init__.
  - `AllowsChildren.__init__` claims positional args as children and forwards
    the remaining kwargs up the MRO.

Note: the parent-tag context stack (sub-issue 3) is OUT OF SCOPE. __enter__
returns self with no side effects; auto-collecting bare Tags inside a with-block
is not implemented here.
"""
from __future__ import annotations

from typing import Any, Self

from htmltools import TagChild


class AllowsChildren:
    children: list[TagChild]

    def __init__(self, *children: TagChild, **kwargs: Any) -> None:
        self.children = list(children)
        super().__init__(**kwargs)

    def append(self, child: TagChild) -> Self:
        self.children.append(child)
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_children.py -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/_children.py pkg-py/tests/shinyui/test_children.py
git commit -m "feat(shinyui): AllowsChildren mixin"
```

---

## Task 4: Bookmark id→instance registry

**Files:**
- Create: `pkg-py/src/shinyui/_bookmark.py`

(No standalone tests — exercised by HasInputValue and bookmark round-trip tests.)

- [ ] **Step 1: Implement the registry**

Create `pkg-py/src/shinyui/_bookmark.py`:

```python
"""Per-session map: input id -> HasInputValue instance.

Attached as `session._shinyui_instances` on first registration. This is a private
attribute on Shiny's Session — acceptable for a prototype; Stage B can negotiate
a public hook in py-shiny.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shiny.session import Session

    from ._input_value import HasInputValue

_ATTR = "_shinyui_instances"


def get_session_instances(session: "Session") -> dict[str, "HasInputValue"]:
    m = getattr(session, _ATTR, None)
    if m is None:
        m = {}
        setattr(session, _ATTR, m)
    return m


def register_instance(session: "Session", id: str, instance: "HasInputValue") -> None:
    get_session_instances(session)[id] = instance


def lookup_instance(session: "Session", id: str) -> "HasInputValue | None":
    return get_session_instances(session).get(id)
```

- [ ] **Step 2: Commit (no tests yet — exercised by HasInputValue next)**

```bash
git add pkg-py/src/shinyui/_bookmark.py
git commit -m "feat(shinyui): per-session id->instance registry"
```

---

## Task 5: `HasInputValue` mixin

**Files:**
- Create: `pkg-py/src/shinyui/_input_value.py`
- Create: `pkg-py/tests/shinyui/test_input_value.py`

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_input_value.py`:

```python
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from htmltools import tags
from shiny._namespaces import ResolvedId

from shinyui._base import UiComponent
from shinyui._bookmark import get_session_instances, lookup_instance
from shinyui._input_value import HasInputValue


class _Pinger(UiComponent, HasInputValue):
    input_handler_name = "test.ping"

    @staticmethod
    def _input_handler(value: Any, name: ResolvedId, session: Any) -> Any:
        return ("pinged", value)

    def tagify(self):
        return tags.div(id=self.id)


class _Plain(UiComponent, HasInputValue):
    """No input_handler — defaults to None."""
    def tagify(self):
        return tags.div(id=self.id)


def test_id_is_stored():
    p = _Plain(id="x")
    assert p.id == "x"


def test_no_session_no_registration():
    """Module-level construction: no session, no registry."""
    _Plain(id="x")  # should not raise


def test_session_registers_self(mock_session):
    p = _Plain(id="x")
    assert lookup_instance(mock_session, "x") is p


def test_register_input_handler_classmethod(monkeypatch):
    captured = {}

    def fake_register(name, fn):
        captured[name] = fn

    monkeypatch.setattr("shinyui._input_value.register_input_handler", fake_register)
    _Pinger._register_input_handler()
    assert captured == {"test.ping": _Pinger._input_handler}


def test_register_input_handler_noop_when_no_handler(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        "shinyui._input_value.register_input_handler",
        lambda n, f: captured.update({n: f}),
    )
    _Plain._register_input_handler()
    assert captured == {}


def test_class_level_bookmark_serializer_inherited():
    class S:
        async def serialize(self, value, state_dir):  # noqa: D401
            return value
        async def deserialize(self, value, state_dir):
            return value

    class _Custom(UiComponent, HasInputValue):
        bookmark_serializer = S()
        def tagify(self):
            return tags.div(id=self.id)

    c = _Custom(id="x")
    assert c._bookmark_serializer is _Custom.bookmark_serializer


def test_per_instance_bookmark_serializer_overrides_class():
    class S:
        async def serialize(self, value, state_dir): return value
        async def deserialize(self, value, state_dir): return value

    class _Custom(UiComponent, HasInputValue):
        bookmark_serializer = S()
        def tagify(self):
            return tags.div(id=self.id)

    inst_ser = S()
    c = _Custom(id="x", bookmark_serializer=inst_ser)
    assert c._bookmark_serializer is inst_ser
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_input_value.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement HasInputValue**

Create `pkg-py/src/shinyui/_input_value.py`:

```python
"""HasInputValue — mixin for components that own a server-readable input id.

Provides:
  - `id: str` (stored on instance)
  - `input_handler_name` and `_input_handler` ClassVars (default to empty / None)
  - `bookmark_serializer` ClassVar default + per-instance override
  - `_register_input_handler()` classmethod for explicit module-load registration
  - id->instance registration on construction (no-op if no session)

Mixin protocol: subclasses MUST call `super().__init__(id=..., **kw)` first.
"""
from __future__ import annotations

from typing import Any, Callable, ClassVar

from shiny._namespaces import ResolvedId  # noqa: F401  (typing reference)
from shiny.bookmark._serializers import Serializer
from shiny.session._session import register_input_handler

from ._bookmark import register_instance


class HasInputValue:
    input_handler_name: ClassVar[str] = ""
    _input_handler: ClassVar[Callable[..., Any] | None] = None
    bookmark_serializer: ClassVar[Serializer | None] = None

    @classmethod
    def _register_input_handler(cls) -> None:
        """Idempotent. Call once at module load if this class declares a handler."""
        if cls.input_handler_name and cls._input_handler is not None:
            register_input_handler(cls.input_handler_name, cls._input_handler)

    def __init__(
        self,
        *,
        id: str,
        bookmark_serializer: Serializer | None = None,
        **kwargs: Any,
    ) -> None:
        self.id = id
        self._bookmark_serializer: Serializer | None = (
            bookmark_serializer if bookmark_serializer is not None else type(self).bookmark_serializer
        )
        super().__init__(**kwargs)
        # After super().__init__: UiComponent has set self._session.
        if self._session is not None:  # type: ignore[attr-defined]
            register_instance(self._session, id, self)  # type: ignore[arg-type]
```

Note on the bookmark serializer type: confirm the precise import path of `Serializer` in the installed Shiny version. If the import line above fails, substitute the appropriate name from `shiny.bookmark`. If unavailable, fall back to `Any`.

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_input_value.py -v`
Expected: All pass. If `Serializer` import fails, adjust to `from shiny.bookmark import Serializer` or use `Any` and re-run.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/_input_value.py pkg-py/tests/shinyui/test_input_value.py
git commit -m "feat(shinyui): HasInputValue mixin + handler registration"
```

---

## Task 6: `Updatable` mixin

**Files:**
- Create: `pkg-py/src/shinyui/_updatable.py`
- Create: `pkg-py/tests/shinyui/test_updatable.py`

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_updatable.py`:

```python
from __future__ import annotations

import pytest
from htmltools import tags

from shinyui._base import UiComponent
from shinyui._updatable import Updatable


class _AbstractStub(UiComponent, Updatable):
    """Does NOT implement update() — should remain abstract."""
    def tagify(self):
        return tags.div()


class _Concrete(UiComponent, Updatable):
    last_kwargs: dict | None = None

    def tagify(self):
        return tags.div()

    def update(self, *, value: int | None = None) -> None:
        type(self).last_kwargs = {"value": value}


def test_abstract_class_cannot_instantiate():
    with pytest.raises(TypeError):
        _AbstractStub()  # type: ignore[abstract]


def test_concrete_class_instantiates():
    c = _Concrete()
    assert c is not None


def test_update_callable_on_concrete():
    c = _Concrete()
    c.update(value=42)
    assert _Concrete.last_kwargs == {"value": 42}
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_updatable.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement Updatable**

Create `pkg-py/src/shinyui/_updatable.py`:

```python
"""Updatable — marker mixin for components that support server-driven update().

`update()` is abstract; concrete subclasses provide a typed `update(*, ...)`
signature with the specific kwargs they accept. No `session=` kwarg — session
is captured by UiComponent.__init__ and resolved at call time via
`self._require_session(for_op="update")`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Updatable(ABC):
    @abstractmethod
    def update(self, **kwargs: Any) -> None: ...
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_updatable.py -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/_updatable.py pkg-py/tests/shinyui/test_updatable.py
git commit -m "feat(shinyui): Updatable abstract mixin"
```

---

## Task 7: Role classes — `UiInput`, `UiOutput`, `UiLayout`

**Files:**
- Create: `pkg-py/src/shinyui/_roles.py`
- Create: `pkg-py/tests/shinyui/test_roles.py`

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_roles.py`:

```python
from __future__ import annotations

from htmltools import tags

from shinyui._base import UiComponent
from shinyui._input_value import HasInputValue
from shinyui._roles import UiInput, UiLayout, UiOutput


class _MyInput(UiInput):
    def tagify(self):
        return tags.div(id=self.id)


class _MyOutput(UiOutput):
    def __init__(self, id: str) -> None:
        self.id = id
        super().__init__()

    def tagify(self):
        return tags.div(id=self.id)


class _MyLayout(UiLayout):
    def tagify(self):
        return tags.div()


def test_uiinput_inherits_uicomponent_and_hasinputvalue():
    inst = _MyInput(id="x")
    assert isinstance(inst, UiComponent)
    assert isinstance(inst, HasInputValue)


def test_uioutput_has_id_attribute():
    inst = _MyOutput(id="y")
    assert inst.id == "y"


def test_uilayout_does_not_have_hasinputvalue_by_default():
    inst = _MyLayout()
    assert not isinstance(inst, HasInputValue)
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_roles.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement role classes**

Create `pkg-py/src/shinyui/_roles.py`:

```python
"""Semantic role classes — UiInput, UiOutput, UiLayout.

These are markers indicating the component's primary purpose. State-bearing
and child-bearing capabilities are provided by orthogonal mixins
(HasInputValue, Updatable, AllowsChildren).
"""
from __future__ import annotations

from ._base import UiComponent
from ._input_value import HasInputValue


class UiInput(UiComponent, HasInputValue):
    """Primarily a user-input control."""


class UiOutput(UiComponent):
    """Primarily a server-rendered output.

    Carries its own `id` attribute (set by subclasses' __init__); does NOT
    inherit HasInputValue (no bookmark serializer, no id->instance map).
    Subclasses that expose read-only signals add accessors directly.
    """


class UiLayout(UiComponent):
    """Primarily a container.

    No id by itself; layouts that expose state add HasInputValue + Updatable.
    """
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_roles.py -v`
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/_roles.py pkg-py/tests/shinyui/test_roles.py
git commit -m "feat(shinyui): UiInput / UiOutput / UiLayout role classes"
```

---

## Task 8: `reactive_calc_method` helper

**Files:**
- Create: `pkg-py/src/shinyui/_reactive.py`
- Create: `pkg-py/tests/shinyui/test_reactive.py`

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_reactive.py`:

```python
from __future__ import annotations

from shiny import reactive

from shinyui._reactive import reactive_calc_method


class _Counter:
    """Tests caching: the wrapped method is invoked once per change."""
    def __init__(self) -> None:
        self.calls = 0

    @reactive_calc_method
    def value(self) -> int:
        self.calls += 1
        return 42


def test_method_returns_value_under_reactive_isolate():
    c = _Counter()
    with reactive.isolate():
        assert c.value() == 42


def test_cached_per_instance():
    """Two different instances should have independent caches."""
    a = _Counter()
    b = _Counter()
    with reactive.isolate():
        assert a.value() == 42
        assert b.value() == 42
    assert a.calls == 1
    assert b.calls == 1
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_reactive.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement reactive_calc_method**

Create `pkg-py/src/shinyui/_reactive.py`:

```python
"""reactive_calc_method — per-instance @reactive.calc decorator.

Inspired by Shiny's `shiny.render._data_frame_utils._reactive_method.reactive_calc_method`.
We hand-roll a small local equivalent (~15 lines) to avoid coupling to a Shiny
private import. Stage B in py-shiny may extract the decorator to a public helper.
"""
from __future__ import annotations

from typing import Any, Callable, TypeVar
from weakref import WeakKeyDictionary

from shiny import reactive

T = TypeVar("T")


def reactive_calc_method(fn: Callable[[Any], T]) -> Callable[[Any], T]:
    cache: WeakKeyDictionary[Any, reactive.Calc_[T]] = WeakKeyDictionary()

    def wrapper(self: Any) -> T:
        calc = cache.get(self)
        if calc is None:
            @reactive.calc
            def _calc() -> T:
                return fn(self)
            calc = _calc
            cache[self] = calc
        return calc()

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_reactive.py -v`
Expected: All pass. If `reactive.Calc_` typing fails, drop the explicit annotation on `cache` (use `WeakKeyDictionary[Any, Any]`).

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/_reactive.py pkg-py/tests/shinyui/test_reactive.py
git commit -m "feat(shinyui): local reactive_calc_method helper"
```

---

## Task 9: `UiInputSlider`

**Files:**
- Create: `pkg-py/src/shinyui/_input_slider.py`
- Create: `pkg-py/tests/shinyui/test_input_slider.py`

**Reference markup source:** `shiny/ui/_input_slider.py` — `input_slider(id, label, min, max, value, step=, ticks=, animate=, width=, sep=, pre=, post=, time_format=, timezone=, drag_range=)`.

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_input_slider.py`:

```python
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import shiny.ui as sui
from htmltools import Tag

from shinyui._input_slider import UiInputSlider, input_slider


def test_factory_returns_instance():
    s = input_slider("n", "N", 1, 100, 50)
    assert isinstance(s, UiInputSlider)
    assert s.id == "n"


def test_tagify_matches_shiny_ui_input_slider():
    ours = input_slider("n", "N", 1, 100, 50).tagify()
    theirs = sui.input_slider("n", "N", 1, 100, 50)
    assert ours.get_html_string() == theirs.get_html_string()


def test_value_accessor_reads_input(mock_session):
    s = input_slider("n", "N", 1, 100, 50)
    mock_session.input.__getitem__.return_value = lambda: 25
    from shiny import reactive
    with reactive.isolate():
        assert s.value() == 25
    mock_session.input.__getitem__.assert_called_with("n")


def test_update_outside_session_raises():
    s = input_slider("n", "N", 1, 100, 50)  # no session at construction
    with pytest.raises(RuntimeError, match=r"UiInputSlider\.update\(\) requires an active session"):
        s.update(value=42)


def test_update_uses_captured_session(mock_session):
    s = input_slider("n", "N", 1, 100, 50)
    s.update(value=42)
    mock_session.send_input_message.assert_called_once()
    name, payload = mock_session.send_input_message.call_args.args
    assert name == "n"
    assert payload["value"] == 42
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_input_slider.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement UiInputSlider**

Read `shiny/ui/_input_slider.py` (run: `uv run python -c "import shiny.ui._input_slider as m; print(m.__file__)"`) to find the markup-construction logic. Copy the Tag-construction body into `tagify()` below, mapping each function argument to `self.<attr>`.

Read `shiny/ui/_input_update.py` (the `update_slider` function) to find the `send_input_message` payload shape for slider updates.

Create `pkg-py/src/shinyui/_input_slider.py`:

```python
"""UiInputSlider — class-based input_slider with typed update() and value() accessor."""
from __future__ import annotations

from typing import Any

from htmltools import Tag

from ._reactive import reactive_calc_method
from ._roles import UiInput
from ._updatable import Updatable

_MISSING = object()


class UiInputSlider(UiInput, Updatable):
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
        animate: bool = False,
        width: str | None = None,
        sep: str = ",",
        pre: str | None = None,
        post: str | None = None,
        time_format: str | None = None,
        timezone: str | None = None,
        drag_range: bool = True,
    ) -> None:
        self.label = label
        self.min = min
        self.max = max
        self.value = value  # NOTE: value attribute is shadowed by value() accessor at class level;
                            # store as _init_value to avoid the collision.
        del self.value
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
        super().__init__(id=id)

    @reactive_calc_method
    def value(self) -> Any:
        return self._read_input()

    def tagify(self) -> Tag:
        # COPY: Reproduce shiny.ui._input_slider.input_slider's Tag construction here.
        # Map each argument to self.<attr>; use self._init_value for the initial value.
        # The shiny source file is at: shiny/ui/_input_slider.py
        import shiny.ui as _sui
        return _sui.input_slider(  # interim: delegate while implementer copies real markup
            self.id, self.label, self.min, self.max, self._init_value,
            step=self.step, ticks=self.ticks, animate=self.animate,
            width=self.width, sep=self.sep, pre=self.pre, post=self.post,
            time_format=self.time_format, timezone=self.timezone, drag_range=self.drag_range,
        )

    def update(
        self,
        *,
        value: Any = _MISSING,
        min: float = _MISSING,  # type: ignore[assignment]
        max: float = _MISSING,  # type: ignore[assignment]
        step: float = _MISSING,  # type: ignore[assignment]
        label: str = _MISSING,  # type: ignore[assignment]
    ) -> None:
        sess = self._require_session(for_op="update")
        msg: dict[str, Any] = {}
        if value is not _MISSING: msg["value"] = value
        if min   is not _MISSING: msg["min"]   = min
        if max   is not _MISSING: msg["max"]   = max
        if step  is not _MISSING: msg["step"]  = step
        if label is not _MISSING: msg["label"] = label
        sess.send_input_message(self.id, msg)


def input_slider(
    id: str,
    label: str,
    min: float,
    max: float,
    value: float | tuple[float, float],
    **kwargs: Any,
) -> UiInputSlider:
    return UiInputSlider(id, label, min, max, value, **kwargs)
```

**Implementer note:** the `tagify()` body above delegates to `shiny.ui.input_slider` as a temporary measure so the snapshot test passes immediately. Replace with a copy-pasted construction body once the test is green (this keeps the prototype dep-free per spec). The snapshot test is the regression net — when you swap the body, re-run the test to confirm equivalence.

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_input_slider.py -v`
Expected: All pass.

- [ ] **Step 5: Inline the tagify markup**

Read `shiny/ui/_input_slider.py` and copy the Tag construction body into `UiInputSlider.tagify()`, replacing the delegation. Re-run the snapshot test:

Run: `uv run pytest pkg-py/tests/shinyui/test_input_slider.py::test_tagify_matches_shiny_ui_input_slider -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyui/_input_slider.py pkg-py/tests/shinyui/test_input_slider.py
git commit -m "feat(shinyui): UiInputSlider + input_slider() factory"
```

---

## Task 10: `UiInputSelect`

**Files:**
- Create: `pkg-py/src/shinyui/_input_select.py`
- Create: `pkg-py/tests/shinyui/test_input_select.py`

**Reference markup source:** `shiny/ui/_input_select.py` — `input_select(id, label, choices, selected=, multiple=, selectize=, width=, size=, remove_button=)`.

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_input_select.py`:

```python
from __future__ import annotations

import pytest
import shiny.ui as sui

from shinyui._input_select import UiInputSelect, input_select


def test_factory_returns_instance():
    s = input_select("col", "Column", {"a": "A", "b": "B"})
    assert isinstance(s, UiInputSelect)


def test_tagify_matches_shiny_ui_input_select():
    ours = input_select("col", "Column", {"a": "A", "b": "B"}).tagify()
    theirs = sui.input_select("col", "Column", {"a": "A", "b": "B"})
    assert ours.get_html_string() == theirs.get_html_string()


def test_value_accessor(mock_session):
    s = input_select("col", "Column", {"a": "A"})
    mock_session.input.__getitem__.return_value = lambda: "a"
    from shiny import reactive
    with reactive.isolate():
        assert s.value() == "a"


def test_update_outside_session_raises():
    s = input_select("col", "Column", {"a": "A"})
    with pytest.raises(RuntimeError):
        s.update(selected="a")


def test_update_sends_message(mock_session):
    s = input_select("col", "Column", {"a": "A"})
    s.update(selected="a")
    mock_session.send_input_message.assert_called_once()
    name, payload = mock_session.send_input_message.call_args.args
    assert name == "col"
    assert payload["value"] == "a"  # shiny.ui.update_select uses "value" key
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_input_select.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement UiInputSelect**

Create `pkg-py/src/shinyui/_input_select.py`:

```python
"""UiInputSelect — class-based input_select."""
from __future__ import annotations

from typing import Any, Mapping

from htmltools import Tag

from ._reactive import reactive_calc_method
from ._roles import UiInput
from ._updatable import Updatable

_MISSING = object()

SelectChoices = Mapping[str, str] | Mapping[str, Mapping[str, str]]


class UiInputSelect(UiInput, Updatable):
    def __init__(
        self,
        id: str,
        label: str,
        choices: SelectChoices,
        *,
        selected: str | tuple[str, ...] | None = None,
        multiple: bool = False,
        selectize: bool = False,
        width: str | None = None,
        size: str | None = None,
        remove_button: bool | None = None,
    ) -> None:
        self.label = label
        self.choices = choices
        self._init_selected = selected
        self.multiple = multiple
        self.selectize = selectize
        self.width = width
        self.size = size
        self.remove_button = remove_button
        super().__init__(id=id)

    @reactive_calc_method
    def value(self) -> Any:
        return self._read_input()

    def tagify(self) -> Tag:
        import shiny.ui as _sui
        # Implementer: copy shiny.ui._input_select markup body here. Interim delegation:
        return _sui.input_select(
            self.id, self.label, self.choices,
            selected=self._init_selected, multiple=self.multiple,
            selectize=self.selectize, width=self.width, size=self.size,
            remove_button=self.remove_button,
        )

    def update(
        self,
        *,
        label: str = _MISSING,           # type: ignore[assignment]
        choices: SelectChoices = _MISSING,  # type: ignore[assignment]
        selected: str | tuple[str, ...] = _MISSING,  # type: ignore[assignment]
    ) -> None:
        sess = self._require_session(for_op="update")
        msg: dict[str, Any] = {}
        if label    is not _MISSING: msg["label"]   = label
        if choices  is not _MISSING: msg["options"] = choices  # Implementer: confirm key vs shiny.ui.update_select
        if selected is not _MISSING: msg["value"]   = selected
        sess.send_input_message(self.id, msg)


def input_select(
    id: str,
    label: str,
    choices: SelectChoices,
    **kwargs: Any,
) -> UiInputSelect:
    return UiInputSelect(id, label, choices, **kwargs)
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_input_select.py -v`
Expected: All pass. If the `update` payload key doesn't match (`options` vs `choices`), check `shiny.ui._input_update.update_select` for the actual key name.

- [ ] **Step 5: Inline tagify markup, re-run snapshot**

Same procedure as Task 9 Step 5.

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyui/_input_select.py pkg-py/tests/shinyui/test_input_select.py
git commit -m "feat(shinyui): UiInputSelect + input_select() factory"
```

---

## Task 11: `UiOutputCode`

**Files:**
- Create: `pkg-py/src/shinyui/_output_code.py`
- Create: `pkg-py/tests/shinyui/test_output_code.py`

**Reference markup source:** `shiny/ui/_output.py` — `output_code(id, placeholder=)`.

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_output_code.py`:

```python
from __future__ import annotations

import shiny.ui as sui

from shinyui._output_code import UiOutputCode, output_code


def test_factory_returns_instance():
    o = output_code("summary")
    assert isinstance(o, UiOutputCode)
    assert o.id == "summary"


def test_tagify_matches_shiny_ui_output_code():
    ours = output_code("summary").tagify()
    theirs = sui.output_code("summary")
    assert ours.get_html_string() == theirs.get_html_string()
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_output_code.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement UiOutputCode**

Create `pkg-py/src/shinyui/_output_code.py`:

```python
"""UiOutputCode — class-based output_code."""
from __future__ import annotations

from typing import Any

from htmltools import Tag

from ._roles import UiOutput


class UiOutputCode(UiOutput):
    def __init__(self, id: str, *, placeholder: bool = False) -> None:
        self.id = id
        self.placeholder = placeholder
        super().__init__()

    def tagify(self) -> Tag:
        import shiny.ui as _sui
        return _sui.output_code(self.id, placeholder=self.placeholder)  # Implementer: inline markup


def output_code(id: str, *, placeholder: bool = False) -> UiOutputCode:
    return UiOutputCode(id, placeholder=placeholder)
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_output_code.py -v`
Expected: All pass.

- [ ] **Step 5: Inline tagify markup, re-run snapshot**

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyui/_output_code.py pkg-py/tests/shinyui/test_output_code.py
git commit -m "feat(shinyui): UiOutputCode + output_code() factory"
```

---

## Task 12: `UiOutputPlot`

**Files:**
- Create: `pkg-py/src/shinyui/_output_plot.py`
- Create: `pkg-py/tests/shinyui/test_output_plot.py`

**Reference markup source:** `shiny/ui/_output.py` — `output_plot(id, width=, height=, inline=, click=, dblclick=, hover=, brush=, fill=)`.

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_output_plot.py`:

```python
from __future__ import annotations

import pytest
import shiny.ui as sui
from shiny import reactive

from shinyui._output_plot import UiOutputPlot, output_plot


def test_factory_returns_instance():
    p = output_plot("p", click=True, brush=True)
    assert isinstance(p, UiOutputPlot)
    assert p.id == "p"


def test_tagify_matches_shiny_ui_output_plot():
    ours = output_plot("p", click=True, brush=True).tagify()
    theirs = sui.output_plot("p", click=True, brush=True)
    assert ours.get_html_string() == theirs.get_html_string()


def test_click_value_reads_correct_id(mock_session):
    p = output_plot("p", click=True)
    mock_session.input.__getitem__.return_value = lambda: {"x": 10, "y": 20}
    with reactive.isolate():
        assert p.click_value() == {"x": 10, "y": 20}
    mock_session.input.__getitem__.assert_called_with("p_click")


def test_brush_value_reads_correct_id(mock_session):
    p = output_plot("p", brush=True)
    mock_session.input.__getitem__.return_value = lambda: {"xmin": 1, "xmax": 2}
    with reactive.isolate():
        assert p.brush_value() == {"xmin": 1, "xmax": 2}
    mock_session.input.__getitem__.assert_called_with("p_brush")


def test_hover_and_dblclick_values(mock_session):
    p = output_plot("p", hover=True, dblclick=True)
    seq = iter([{"x": 1}, {"x": 2}])
    mock_session.input.__getitem__.return_value = lambda: next(seq)
    with reactive.isolate():
        assert p.hover_value()    == {"x": 1}
        assert p.dblclick_value() == {"x": 2}


def test_no_update_method():
    p = output_plot("p")
    assert not hasattr(p, "update")


def test_no_input_handlers_registered_for_plot(monkeypatch):
    """Plot should not call register_input_handler in its module."""
    # Re-import to confirm no side effects beyond the import.
    import importlib
    import shinyui._output_plot as m
    importlib.reload(m)
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_output_plot.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement UiOutputPlot**

Create `pkg-py/src/shinyui/_output_plot.py`:

```python
"""UiOutputPlot — output with read-only client-side interaction signals.

Derived input ids:
  input.<id>_click       — {x, y} | None
  input.<id>_dblclick    — {x, y} | None
  input.<id>_hover       — {x, y} | None
  input.<id>_brush       — {xmin, xmax, ymin, ymax, ...} | None

Plot does NOT use HasInputValue. Derived inputs flow through Shiny's
auto-created Value[Any] mechanism on first session.input[...] access; no
custom input handlers are registered for these wire types.
"""
from __future__ import annotations

from typing import Any

from htmltools import Tag

from ._reactive import reactive_calc_method
from ._roles import UiOutput


class UiOutputPlot(UiOutput):
    def __init__(
        self,
        id: str,
        *,
        width: str = "100%",
        height: str = "400px",
        inline: bool = False,
        click: bool = False,
        dblclick: bool = False,
        hover: bool = False,
        brush: bool = False,
        fill: bool = False,
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
        super().__init__()

    @reactive_calc_method
    def click_value(self) -> Any:    return self._read_input("_click")

    @reactive_calc_method
    def dblclick_value(self) -> Any: return self._read_input("_dblclick")

    @reactive_calc_method
    def hover_value(self) -> Any:    return self._read_input("_hover")

    @reactive_calc_method
    def brush_value(self) -> Any:    return self._read_input("_brush")

    def tagify(self) -> Tag:
        import shiny.ui as _sui
        return _sui.output_plot(
            self.id, width=self.width, height=self.height, inline=self.inline,
            click=self.click_enabled, dblclick=self.dblclick_enabled,
            hover=self.hover_enabled, brush=self.brush_enabled, fill=self.fill,
        )


def output_plot(id: str, **kwargs: Any) -> UiOutputPlot:
    return UiOutputPlot(id, **kwargs)
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_output_plot.py -v`
Expected: All pass.

- [ ] **Step 5: Inline tagify markup, re-run snapshot**

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyui/_output_plot.py pkg-py/tests/shinyui/test_output_plot.py
git commit -m "feat(shinyui): UiOutputPlot with read-only signal accessors"
```

---

## Task 13: `UiAccordionPanel`

**Files:**
- Create: `pkg-py/src/shinyui/_accordion_panel.py`
- Create: `pkg-py/tests/shinyui/test_accordion_panel.py`

**Reference markup source:** `shiny/ui/_accordion.py` — `accordion_panel(title, *args, value=, icon=)`.

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_accordion_panel.py`:

```python
from __future__ import annotations

import shiny.ui as sui
from htmltools import tags

from shinyui._accordion_panel import UiAccordionPanel, accordion_panel
from shinyui._children import AllowsChildren


def test_factory_returns_instance():
    p = accordion_panel("Settings", "body")
    assert isinstance(p, UiAccordionPanel)
    assert isinstance(p, AllowsChildren)


def test_children_collected():
    p = accordion_panel("Settings", "a", "b")
    assert "a" in p.children and "b" in p.children


def test_tagify_matches_shiny():
    ours = accordion_panel("Settings", "body").tagify()
    theirs = sui.accordion_panel("Settings", "body")
    assert ours.get_html_string() == theirs.get_html_string()


def test_with_block_appends():
    with accordion_panel("Settings") as p:
        p.append(tags.p("inside"))
    assert len(p.children) == 1
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_accordion_panel.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement UiAccordionPanel**

Create `pkg-py/src/shinyui/_accordion_panel.py`:

```python
"""UiAccordionPanel — layout child of UiAccordion."""
from __future__ import annotations

from typing import Any

from htmltools import Tag, TagChild

from ._children import AllowsChildren
from ._roles import UiLayout


class UiAccordionPanel(UiLayout, AllowsChildren):
    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | None = None,
        icon: TagChild | None = None,
    ) -> None:
        self.title = title
        self._value = value
        self.icon = icon
        super().__init__(*args)

    @property
    def value(self) -> str:
        return self._value if self._value is not None else self.title

    def tagify(self) -> Tag:
        import shiny.ui as _sui
        return _sui.accordion_panel(
            self.title, *self.children, value=self._value, icon=self.icon,
        )


def accordion_panel(title: str, *args: TagChild, **kwargs: Any) -> UiAccordionPanel:
    return UiAccordionPanel(title, *args, **kwargs)
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_accordion_panel.py -v`
Expected: All pass.

- [ ] **Step 5: Inline tagify markup, re-run snapshot**

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyui/_accordion_panel.py pkg-py/tests/shinyui/test_accordion_panel.py
git commit -m "feat(shinyui): UiAccordionPanel + accordion_panel() factory"
```

---

## Task 14: `UiAccordion`

**Files:**
- Create: `pkg-py/src/shinyui/_accordion.py`
- Create: `pkg-py/tests/shinyui/test_accordion.py`

**Reference markup source:** `shiny/ui/_accordion.py` — `accordion(*args, id=None, open=None, multiple=True, class_=None, width=None, height=None)`.

Read `shiny/_input_handler.py` (or wherever `input_handlers` is registered) to find the handler name registered for accordion. Common candidate: `"shiny.bindings.accordion"` or `"shinyAccordion"`. Use that exact string for `input_handler_name`. Read `shiny.ui._input_update.update_accordion` to find the update payload shape.

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_accordion.py`:

```python
from __future__ import annotations

import pytest
import shiny.ui as sui
from shiny import reactive

from shinyui._accordion import UiAccordion, accordion
from shinyui._accordion_panel import accordion_panel
from shinyui._children import AllowsChildren
from shinyui._input_value import HasInputValue
from shinyui._updatable import Updatable


def test_factory_returns_instance():
    a = accordion(accordion_panel("A"), accordion_panel("B"), id="acc")
    assert isinstance(a, UiAccordion)
    assert isinstance(a, HasInputValue)
    assert isinstance(a, AllowsChildren)
    assert isinstance(a, Updatable)


def test_tagify_matches_shiny():
    ours = accordion(
        accordion_panel("A", "body-a"), accordion_panel("B", "body-b"),
        id="acc", open="A",
    ).tagify()
    theirs = sui.accordion(
        sui.accordion_panel("A", "body-a"), sui.accordion_panel("B", "body-b"),
        id="acc", open="A",
    )
    assert ours.get_html_string() == theirs.get_html_string()


def test_open_panels_accessor(mock_session):
    a = accordion(accordion_panel("A"), id="acc")
    mock_session.input.__getitem__.return_value = lambda: ["A"]
    with reactive.isolate():
        assert a.open_panels() == ("A",)


def test_update_outside_session_raises():
    a = accordion(accordion_panel("A"), id="acc")
    with pytest.raises(RuntimeError):
        a.update(open=("A",))


def test_update_sends_message(mock_session):
    a = accordion(accordion_panel("A"), accordion_panel("B"), id="acc")
    a.update(open=("A", "B"))
    mock_session.send_input_message.assert_called_once()


def test_input_handler_is_registered_after_import():
    from shiny._input_handler import input_handlers
    # input_handler_name is the wire-type for accordion (verify against shiny source).
    assert UiAccordion.input_handler_name in input_handlers._handlers
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_accordion.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement UiAccordion**

Create `pkg-py/src/shinyui/_accordion.py`:

```python
"""UiAccordion — layout with multiple panels; exposes open-panel set as input value."""
from __future__ import annotations

from typing import Any

from htmltools import Tag

from ._children import AllowsChildren
from ._input_value import HasInputValue
from ._reactive import reactive_calc_method
from ._roles import UiLayout
from ._updatable import Updatable

_MISSING = object()


def _accordion_input_handler(value: Any, name: Any, session: Any) -> Any:
    """Coerce accordion's open-panel list into a tuple for tidy server use."""
    return tuple(value) if value is not None else ()


class UiAccordion(UiLayout, AllowsChildren, HasInputValue, Updatable):
    # IMPLEMENTER: Confirm the exact wire-type string by reading shiny.ui._accordion.py
    # for `register_input_handler("...", ...)`. Adjust the literal below if wrong;
    # the test_input_handler_is_registered_after_import test pins it.
    input_handler_name: ClassVar[str] = "shiny.bindings.accordion"
    _input_handler = staticmethod(_accordion_input_handler)

    def __init__(
        self,
        *args: Any,
        id: str,
        open: str | tuple[str, ...] | bool | None = None,
        multiple: bool = True,
        class_: str | None = None,
        width: str | None = None,
        height: str | None = None,
    ) -> None:
        self._open = open
        self.multiple = multiple
        self.class_ = class_
        self.width = width
        self.height = height
        super().__init__(*args, id=id)

    @reactive_calc_method
    def open_panels(self) -> tuple[str, ...]:
        return tuple(self._read_input() or ())

    def tagify(self) -> Tag:
        import shiny.ui as _sui
        return _sui.accordion(
            *self.children, id=self.id, open=self._open, multiple=self.multiple,
            class_=self.class_, width=self.width, height=self.height,
        )

    def update(
        self,
        *,
        open: tuple[str, ...] = _MISSING,    # type: ignore[assignment]
        show: tuple[str, ...] = _MISSING,    # type: ignore[assignment]
        hide: tuple[str, ...] = _MISSING,    # type: ignore[assignment]
    ) -> None:
        sess = self._require_session(for_op="update")
        # IMPLEMENTER: read shiny.ui._input_update.update_accordion for the exact payload shape.
        # The accordion update protocol uses methods like "set", "open", "close" — confirm.
        msg: dict[str, Any] = {}
        if open is not _MISSING: msg["method"] = "set"; msg["values"] = list(open)
        if show is not _MISSING: msg["method"] = "open"; msg["values"] = list(show)
        if hide is not _MISSING: msg["method"] = "close"; msg["values"] = list(hide)
        sess.send_input_message(self.id, msg)


UiAccordion._register_input_handler()


def accordion(*args: Any, id: str, **kwargs: Any) -> UiAccordion:
    return UiAccordion(*args, id=id, **kwargs)
```

Add the missing `ClassVar` import:

```python
from typing import Any, ClassVar
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_accordion.py -v`
Expected: All pass. If `input_handler_name` is wrong, read `shiny/ui/_accordion.py` and `shiny/_input_handler.py` to find the actual handler name, fix, and re-run.

- [ ] **Step 5: Inline tagify markup, re-run snapshot**

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyui/_accordion.py pkg-py/tests/shinyui/test_accordion.py
git commit -m "feat(shinyui): UiAccordion + accordion() factory"
```

---

## Task 15: `UiCard`

**Files:**
- Create: `pkg-py/src/shinyui/_card.py`
- Create: `pkg-py/tests/shinyui/test_card.py`

**Reference markup source:** `shiny/ui/_card.py` — `card(*args, full_screen=False, height=None, max_height=None, min_height=None, fill=True, class_=None, id=None, **kwargs)`.

Card's wire input for `full_screen` may not exist in stock shiny. This prototype introduces it: the rendered card includes a data-attribute or JS hook that pushes `input.<card_id>()` = bool. **For the prototype, do not worry about the client-side JS plumbing** — the snapshot test compares markup to `shiny.ui.card`, which won't emit a binding; the `full_screen_value()` accessor is tested by mocking `session.input` directly. Real client-side wiring is out of scope for Stage A (would be Stage B work).

- [ ] **Step 1: Write failing tests**

Create `pkg-py/tests/shinyui/test_card.py`:

```python
from __future__ import annotations

import pytest
import shiny.ui as sui
from shiny import reactive

from shinyui._card import UiCard, card
from shinyui._children import AllowsChildren
from shinyui._input_value import HasInputValue
from shinyui._updatable import Updatable


def test_factory_returns_instance():
    c = card("body", id="main")
    assert isinstance(c, UiCard)
    assert isinstance(c, HasInputValue)
    assert isinstance(c, AllowsChildren)
    assert isinstance(c, Updatable)


def test_tagify_matches_shiny():
    ours = card("body", id="main", full_screen=False).tagify()
    theirs = sui.card("body", id="main", full_screen=False)
    assert ours.get_html_string() == theirs.get_html_string()


def test_full_screen_value(mock_session):
    c = card("body", id="main")
    mock_session.input.__getitem__.return_value = lambda: True
    with reactive.isolate():
        assert c.full_screen_value() is True
    mock_session.input.__getitem__.assert_called_with("main")


def test_update_outside_session_raises():
    c = card("body", id="main")
    with pytest.raises(RuntimeError):
        c.update(full_screen=True)


def test_update_sends_message(mock_session):
    c = card("body", id="main")
    c.update(full_screen=True)
    mock_session.send_input_message.assert_called_once_with("main", {"full_screen": True})
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `uv run pytest pkg-py/tests/shinyui/test_card.py -v`
Expected: All fail with `ModuleNotFoundError`.

- [ ] **Step 3: Implement UiCard**

Create `pkg-py/src/shinyui/_card.py`:

```python
"""UiCard — layout with optional full-screen toggle exposed as input value."""
from __future__ import annotations

from typing import Any

from htmltools import Tag, TagChild

from ._children import AllowsChildren
from ._input_value import HasInputValue
from ._reactive import reactive_calc_method
from ._roles import UiLayout
from ._updatable import Updatable

_MISSING = object()


class UiCard(UiLayout, AllowsChildren, HasInputValue, Updatable):
    # No input_handler_name / _input_handler — card's full_screen is a plain JSON bool.

    def __init__(
        self,
        *args: TagChild,
        id: str,
        full_screen: bool = False,
        height: str | None = None,
        max_height: str | None = None,
        min_height: str | None = None,
        fill: bool = True,
        class_: str | None = None,
    ) -> None:
        self._full_screen = full_screen
        self.height = height
        self.max_height = max_height
        self.min_height = min_height
        self.fill = fill
        self.class_ = class_
        super().__init__(*args, id=id)

    @reactive_calc_method
    def full_screen_value(self) -> bool:
        return bool(self._read_input())

    def tagify(self) -> Tag:
        import shiny.ui as _sui
        return _sui.card(
            *self.children, full_screen=self._full_screen, height=self.height,
            max_height=self.max_height, min_height=self.min_height, fill=self.fill,
            class_=self.class_, id=self.id,
        )

    def update(
        self,
        *,
        full_screen: bool = _MISSING,  # type: ignore[assignment]
    ) -> None:
        sess = self._require_session(for_op="update")
        msg: dict[str, Any] = {}
        if full_screen is not _MISSING: msg["full_screen"] = full_screen
        sess.send_input_message(self.id, msg)


def card(*args: TagChild, id: str, **kwargs: Any) -> UiCard:
    return UiCard(*args, id=id, **kwargs)
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `uv run pytest pkg-py/tests/shinyui/test_card.py -v`
Expected: All pass.

- [ ] **Step 5: Inline tagify markup, re-run snapshot**

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyui/_card.py pkg-py/tests/shinyui/test_card.py
git commit -m "feat(shinyui): UiCard with full_screen_value() and update()"
```

---

## Task 16: Public exports

**Files:**
- Modify: `pkg-py/src/shinyui/__init__.py`

- [ ] **Step 1: Write failing test**

Create `pkg-py/tests/shinyui/test_public_exports.py`:

```python
def test_public_exports():
    import shinyui as sui

    # Class names
    assert sui.UiComponent
    assert sui.UiInput and sui.UiOutput and sui.UiLayout
    assert sui.HasInputValue and sui.Updatable and sui.AllowsChildren
    assert sui.UiInputSlider and sui.UiInputSelect
    assert sui.UiOutputCode and sui.UiOutputPlot
    assert sui.UiCard and sui.UiAccordion and sui.UiAccordionPanel

    # Factory names
    assert callable(sui.input_slider)
    assert callable(sui.input_select)
    assert callable(sui.output_code)
    assert callable(sui.output_plot)
    assert callable(sui.card)
    assert callable(sui.accordion)
    assert callable(sui.accordion_panel)
```

- [ ] **Step 2: Run test — verify it fails**

Run: `uv run pytest pkg-py/tests/shinyui/test_public_exports.py -v`
Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Update __init__.py**

Replace `pkg-py/src/shinyui/__init__.py` with:

```python
"""shinyui — prototype class-per-component UI hierarchy.

See docs/superpowers/specs/2026-05-13-shinyui-metadata-consolidation-design.md.
"""
from ._accordion import UiAccordion, accordion
from ._accordion_panel import UiAccordionPanel, accordion_panel
from ._base import UiComponent
from ._card import UiCard, card
from ._children import AllowsChildren
from ._input_select import UiInputSelect, input_select
from ._input_slider import UiInputSlider, input_slider
from ._input_value import HasInputValue
from ._output_code import UiOutputCode, output_code
from ._output_plot import UiOutputPlot, output_plot
from ._roles import UiInput, UiLayout, UiOutput
from ._updatable import Updatable

__all__ = [
    # Bases / mixins
    "UiComponent", "UiInput", "UiOutput", "UiLayout",
    "HasInputValue", "Updatable", "AllowsChildren",
    # Concrete classes
    "UiInputSlider", "UiInputSelect",
    "UiOutputCode", "UiOutputPlot",
    "UiCard", "UiAccordion", "UiAccordionPanel",
    # Factories
    "input_slider", "input_select",
    "output_code", "output_plot",
    "card", "accordion", "accordion_panel",
]
```

- [ ] **Step 4: Run test — verify it passes**

Run: `uv run pytest pkg-py/tests/shinyui/test_public_exports.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyui/__init__.py pkg-py/tests/shinyui/test_public_exports.py
git commit -m "feat(shinyui): public exports"
```

---

## Task 17: Cross-cutting hierarchy tests

**Files:**
- Create: `pkg-py/tests/shinyui/test_hierarchy.py`
- Create: `pkg-py/tests/shinyui/test_allows_children.py`
- Create: `pkg-py/tests/shinyui/test_input_handler_registration.py`
- Create: `pkg-py/tests/shinyui/test_update_resolution.py`
- Create: `pkg-py/tests/shinyui/test_read_accessors.py`

- [ ] **Step 1: Write test_hierarchy.py**

Create `pkg-py/tests/shinyui/test_hierarchy.py`:

```python
from __future__ import annotations

import pytest

import shinyui as sui


def _maker(cls):
    """Build a representative instance of `cls` with whatever args its factory needs."""
    if cls is sui.UiInputSlider:    return sui.input_slider("n", "N", 1, 10, 5)
    if cls is sui.UiInputSelect:    return sui.input_select("c", "C", {"a": "A"})
    if cls is sui.UiOutputCode:     return sui.output_code("o")
    if cls is sui.UiOutputPlot:     return sui.output_plot("p")
    if cls is sui.UiCard:           return sui.card("b", id="m")
    if cls is sui.UiAccordion:      return sui.accordion(sui.accordion_panel("A"), id="acc")
    if cls is sui.UiAccordionPanel: return sui.accordion_panel("X", "y")
    raise AssertionError(f"no maker for {cls}")


ALL_CLASSES = [
    sui.UiInputSlider, sui.UiInputSelect,
    sui.UiOutputCode, sui.UiOutputPlot,
    sui.UiCard, sui.UiAccordion, sui.UiAccordionPanel,
]


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_is_uicomponent(cls):
    assert isinstance(_maker(cls), sui.UiComponent)


@pytest.mark.parametrize("cls,expected", [
    (sui.UiInputSlider,    {sui.UiInput, sui.HasInputValue, sui.Updatable}),
    (sui.UiInputSelect,    {sui.UiInput, sui.HasInputValue, sui.Updatable}),
    (sui.UiOutputCode,     {sui.UiOutput}),
    (sui.UiOutputPlot,     {sui.UiOutput}),
    (sui.UiCard,           {sui.UiLayout, sui.AllowsChildren, sui.HasInputValue, sui.Updatable}),
    (sui.UiAccordion,      {sui.UiLayout, sui.AllowsChildren, sui.HasInputValue, sui.Updatable}),
    (sui.UiAccordionPanel, {sui.UiLayout, sui.AllowsChildren}),
])
def test_expected_bases(cls, expected):
    inst = _maker(cls)
    for base in expected:
        assert isinstance(inst, base), f"{cls.__name__} should be instance of {base.__name__}"


@pytest.mark.parametrize("cls,allows_children", [
    (sui.UiInputSlider,    False),
    (sui.UiInputSelect,    False),
    (sui.UiOutputCode,     False),
    (sui.UiOutputPlot,     False),
    (sui.UiCard,           True),
    (sui.UiAccordion,      True),
    (sui.UiAccordionPanel, True),
])
def test_with_block_protocol(cls, allows_children):
    inst = _maker(cls)
    if allows_children:
        with inst as ctx:
            assert ctx is inst
    else:
        with pytest.raises(TypeError, match=f"{cls.__name__} does not accept children"):
            inst.__enter__()
```

- [ ] **Step 2: Write test_allows_children.py**

Create `pkg-py/tests/shinyui/test_allows_children.py`:

```python
from __future__ import annotations

from htmltools import tags

import shinyui as sui


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


def test_bare_tag_in_with_block_is_not_auto_collected():
    """Tag-as-CM is sub-issue 3 (out of scope for this prototype)."""
    with sui.card(id="m") as c:
        tags.p("not collected")  # noqa: B018  intentional bare expr
    assert c.children == []
```

- [ ] **Step 3: Write test_input_handler_registration.py**

Create `pkg-py/tests/shinyui/test_input_handler_registration.py`:

```python
from __future__ import annotations

from shiny._input_handler import input_handlers

import shinyui as sui


def test_accordion_handler_registered_after_import():
    assert sui.UiAccordion.input_handler_name in input_handlers._handlers


def test_slider_does_not_register_handler():
    """Slider has no custom server-side wire coercion."""
    assert sui.UiInputSlider.input_handler_name == ""
    assert sui.UiInputSlider._input_handler is None


def test_card_does_not_register_handler():
    assert sui.UiCard.input_handler_name == ""
```

- [ ] **Step 4: Write test_update_resolution.py**

Create `pkg-py/tests/shinyui/test_update_resolution.py`:

```python
from __future__ import annotations

import pytest

import shinyui as sui


@pytest.mark.parametrize("maker", [
    lambda: sui.input_slider("n", "N", 1, 10, 5),
    lambda: sui.input_select("c", "C", {"a": "A"}),
    lambda: sui.card("b", id="m"),
    lambda: sui.accordion(sui.accordion_panel("A"), id="acc"),
])
def test_update_raises_outside_session(maker):
    inst = maker()
    with pytest.raises(RuntimeError, match=r"requires an active session"):
        inst.update()


def test_update_uses_captured_session(mock_session):
    s = sui.input_slider("n", "N", 1, 10, 5)
    s.update(value=7)
    mock_session.send_input_message.assert_called_once()


def test_update_no_session_kwarg():
    """update() must not accept a `session=` kwarg."""
    s = sui.input_slider("n", "N", 1, 10, 5)
    import inspect
    sig = inspect.signature(s.update)
    assert "session" not in sig.parameters
```

- [ ] **Step 5: Write test_read_accessors.py**

Create `pkg-py/tests/shinyui/test_read_accessors.py`:

```python
from __future__ import annotations

import pytest
from shiny import reactive

import shinyui as sui


@pytest.mark.parametrize("maker,accessor,suffix,value", [
    (lambda: sui.input_slider("n", "N", 1, 10, 5), "value",            "",         7),
    (lambda: sui.input_select("c", "C", {"a": "A"}), "value",          "",         "a"),
    (lambda: sui.card("b", id="m"),                  "full_screen_value", "",     True),
    (lambda: sui.accordion(sui.accordion_panel("A"), id="acc"),
                                                     "open_panels",    "",         ["A"]),
    (lambda: sui.output_plot("p", click=True),       "click_value",    "_click",   {"x": 1, "y": 2}),
    (lambda: sui.output_plot("p", brush=True),       "brush_value",    "_brush",   {"xmin": 1}),
])
def test_accessor_reads_correct_id(mock_session, maker, accessor, suffix, value):
    inst = maker()
    expected_id = f"{inst.id}{suffix}"
    mock_session.input.__getitem__.return_value = lambda: value
    with reactive.isolate():
        result = getattr(inst, accessor)()
    if isinstance(value, list):
        assert result == tuple(value)
    else:
        assert result == value
    mock_session.input.__getitem__.assert_called_with(expected_id)


@pytest.mark.parametrize("maker,accessor", [
    (lambda: sui.input_slider("n", "N", 1, 10, 5),   "value"),
    (lambda: sui.card("b", id="m"),                  "full_screen_value"),
    (lambda: sui.output_plot("p", click=True),       "click_value"),
])
def test_accessor_raises_outside_session(maker, accessor):
    inst = maker()
    with pytest.raises(RuntimeError, match=r"requires an active session"):
        with reactive.isolate():
            getattr(inst, accessor)()
```

- [ ] **Step 6: Run all cross-cutting tests**

Run: `uv run pytest pkg-py/tests/shinyui/test_hierarchy.py pkg-py/tests/shinyui/test_allows_children.py pkg-py/tests/shinyui/test_input_handler_registration.py pkg-py/tests/shinyui/test_update_resolution.py pkg-py/tests/shinyui/test_read_accessors.py -v`

Expected: All pass. If a test fails, fix the relevant class implementation — the cross-cutting tests are pinning behavior the per-class tests should already have caught.

- [ ] **Step 7: Commit**

```bash
git add pkg-py/tests/shinyui/test_hierarchy.py pkg-py/tests/shinyui/test_allows_children.py pkg-py/tests/shinyui/test_input_handler_registration.py pkg-py/tests/shinyui/test_update_resolution.py pkg-py/tests/shinyui/test_read_accessors.py
git commit -m "test(shinyui): cross-cutting hierarchy + lifecycle tests"
```

---

## Task 18: Bookmark round-trip integration test

**Files:**
- Create: `pkg-py/tests/shinyui/test_bookmark_roundtrip.py`

- [ ] **Step 1: Write failing test**

Create `pkg-py/tests/shinyui/test_bookmark_roundtrip.py`:

```python
"""End-to-end bookmark round-trip for class-owned serializers.

Constructs a HasInputValue subclass with a custom serializer, simulates
save (via the registered instance map) and restore (by lookup).
"""
from __future__ import annotations

from typing import Any

from shinyui._bookmark import lookup_instance

import shinyui as sui


def test_session_registry_records_instance_on_construction(mock_session):
    s = sui.input_slider("n", "N", 1, 10, 5)
    assert lookup_instance(mock_session, "n") is s


def test_accordion_serializer_round_trip(mock_session):
    """Accordion's class-owned input_handler returns a tuple; restoring should re-tuple."""
    a = sui.accordion(sui.accordion_panel("A"), sui.accordion_panel("B"), id="acc")
    # The serializer + handler path is exercised via the wire layer; here we
    # verify that the accordion instance is reachable from its id on the session.
    assert lookup_instance(mock_session, "acc") is a


def test_per_instance_serializer_override():
    class Custom:
        async def serialize(self, value: Any, state_dir: Any) -> Any: return value
        async def deserialize(self, value: Any, state_dir: Any) -> Any: return value

    custom = Custom()
    s = sui.input_slider("n", "N", 1, 10, 5)
    s._bookmark_serializer = custom
    assert s._bookmark_serializer is custom


def test_no_session_no_registry_noop():
    """Construction without a session must not raise."""
    s = sui.input_slider("n", "N", 1, 10, 5)
    assert s._session is None
```

- [ ] **Step 2: Run test**

Run: `uv run pytest pkg-py/tests/shinyui/test_bookmark_roundtrip.py -v`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/tests/shinyui/test_bookmark_roundtrip.py
git commit -m "test(shinyui): bookmark id->instance round-trip"
```

---

## Task 19: Example app `14-unified-ui-prototype`

**Files:**
- Create: `examples/app-py/14-unified-ui-prototype/app.py`
- Create: `examples/app-py/14-unified-ui-prototype/README.md`

- [ ] **Step 1: Write the example app**

Create `examples/app-py/14-unified-ui-prototype/app.py`:

```python
"""End-to-end demo of shinyui's class-per-component hierarchy.

Exercises every reference class in one page:
  - UiInputSlider, UiInputSelect  (simple + structured inputs)
  - UiOutputCode                  (output)
  - UiOutputPlot                  (output with read-only signals)
  - UiCard                        (layout with state)
  - UiAccordion + UiAccordionPanel (layout-with-state + layout-as-child)

The `app_ui` is a function (not a module-level Tag) so a session is in scope
when components are constructed — this is what enables class-owned bookmark
serializers to register themselves.
"""
from __future__ import annotations

import io

import matplotlib.pyplot as plt
import numpy as np
from shiny import App, Inputs, Outputs, Session, reactive, render

import shinyui as sui


def app_ui(request):
    return sui.card(
        sui.input_slider("n", "Sample size", 10, 1000, 100),
        sui.input_select("dist", "Distribution",
                         {"normal": "Normal", "uniform": "Uniform"}),
        sui.output_code("summary"),
        sui.output_plot("plot", click=True, brush=True),
        sui.accordion(
            sui.accordion_panel(
                "Settings",
                sui.input_slider("seed", "Seed", 1, 1000, 42),
            ),
            sui.accordion_panel(
                "Diagnostics",
                sui.output_code("diag"),
            ),
            id="acc",
            open="Settings",
        ),
        id="main_card",
        full_screen=False,
    )


def server(input: Inputs, output: Outputs, session: Session):

    @reactive.calc
    def data() -> np.ndarray:
        rng = np.random.default_rng(input.seed())
        if input.dist() == "normal":
            return rng.standard_normal(input.n())
        return rng.uniform(-2, 2, input.n())

    @render.code
    def summary():
        x = data()
        return f"n = {len(x)}\nmean = {x.mean():.3f}\nstd = {x.std():.3f}"

    @render.plot
    def plot():
        fig, ax = plt.subplots()
        ax.hist(data(), bins=30)
        return fig

    @render.code
    def diag():
        return f"open panels = {accordion.open_panels()}"

    # --- Demonstrating .value() / .click_value() / .full_screen_value() ---
    @reactive.effect
    def _():
        coords = plot.click_value()
        if coords is not None:
            print(f"click @ {coords['x']},{coords['y']}")

    @reactive.effect
    def _():
        b = plot.brush_value()
        if b is not None:
            print(f"brush: {b}")

    # --- Server-driven .update() on layouts-with-state ---
    @reactive.effect
    def _():
        # When n exceeds 800, auto-expand the main card and reveal Diagnostics.
        if input.n() > 800:
            main_card.update(full_screen=True)
            accordion.update(open=("Settings", "Diagnostics"))


app = App(app_ui, server)
```

**Note:** The example references `plot`, `main_card`, `accordion` inside `server()`. Those names must be in scope. Two implementation paths:

1. Capture them in the `app_ui` function's closure and re-construct in `server()` via session-attached lookup (less ergonomic).
2. Construct them inside `server()` directly (preferred for the prototype — see the simpler structure below).

If the closure capture pattern is too awkward, refactor `app.py` so `server()` builds its own component handles by id-lookup on the session's `_shinyui_instances` map:

```python
def server(input, output, session):
    plot       = sui.lookup_component(session, "plot")        # add this helper to _bookmark.py
    main_card  = sui.lookup_component(session, "main_card")
    accordion  = sui.lookup_component(session, "acc")
    ...
```

If `lookup_component` is desired, add it to `pkg-py/src/shinyui/_bookmark.py` as a thin wrapper around `lookup_instance` and export from `__init__.py`. Otherwise, build a closure-capture pattern documented in the README.

- [ ] **Step 2: Write the README**

Create `examples/app-py/14-unified-ui-prototype/README.md`:

```markdown
# 14 — Unified UI prototype

Stage A demo of [shinyui](../../../pkg-py/src/shinyui), the class-per-component
UI hierarchy that consolidates each component's metadata (handler, serializer,
HTML deps, `update()`, read accessors) onto a single class.

Run:

    uv run shiny run examples/app-py/14-unified-ui-prototype/app.py

## What this demonstrates

| Archetype | Class | Demonstrated by |
|---|---|---|
| Simple input | `UiInputSlider` | `n` and `seed` sliders |
| Structured input | `UiInputSelect` | `dist` selector |
| Plain output | `UiOutputCode` | `summary` and `diag` |
| Output with read-only signals | `UiOutputPlot` | `plot` with `click=True, brush=True` |
| Layout with children | `UiCard` | `main_card` |
| Layout with state + children | `UiCard` + `UiAccordion` | `main_card.full_screen_value()`, `accordion.open_panels()` |
| Layout-as-child | `UiAccordionPanel` | Two panels inside `accordion` |

## What to try

- Drag the sliders — `summary` recomputes.
- Click on the plot — coordinates appear in the server log via `plot.click_value()`.
- Brush a region — `plot.brush_value()` fires.
- Set `n > 800` — the card auto-expands to full-screen and both accordion panels open
  via `.update()` calls from the server.

## Bookmark round-trip

Append `?_inputs_=...` to the URL or use Shiny's built-in URL bookmark. Class-owned
serializers (e.g. `UiAccordion`'s) restore correctly because the components
register themselves with the session during `app_ui(request)` construction.
```

- [ ] **Step 3: Smoke-test the example**

Run: `uv run shiny run examples/app-py/14-unified-ui-prototype/app.py --port 8765 &` then `curl -s http://localhost:8765/ | head -50` and kill the process.

Expected: HTML page loads without 500 errors. If errors occur, fix the underlying issue (most likely `lookup_component` or the closure pattern needs the inline-construction approach).

- [ ] **Step 4: Commit**

```bash
git add examples/app-py/14-unified-ui-prototype
git commit -m "feat(shinyui): example app exercising the full reference set"
```

---

## Task 20: Final integration

- [ ] **Step 1: Run full check**

Run: `make py-check`
Expected: All green — pyright clean, ruff clean, all tests pass.

- [ ] **Step 2: Update docs/features.md and docs/todos.md**

If `docs/features.md` has a section listing feature surfaces, add a "shinyui prototype (#69 Stage A)" entry pointing at the example app and design doc. If `docs/todos.md` had a placeholder for unified-UI work, replace it with a note that Stage A is complete and the next step is Stage B (port to py-shiny).

Read the files first to confirm shape; if no obvious entry point exists, skip this step and note it in the commit message.

- [ ] **Step 3: Final commit**

```bash
git add docs/features.md docs/todos.md  # if updated
git commit -m "docs: note shinyui Stage A completion (#69)"  # if applicable
```

- [ ] **Step 4: Verify acceptance criteria**

Walk the acceptance list from the spec and confirm each is met:

- [ ] `pkg-py/src/shinyui/` exists with all bases, mixins, role classes, and seven concrete classes
- [ ] Each class has a factory exported alongside
- [ ] `examples/app-py/14-unified-ui-prototype/` runs and demonstrates bookmark + `.update()`
- [ ] All test files exist and pass
- [ ] `tagify()` snapshots match `shiny.ui.*` markup for every concrete class
- [ ] `with UiInputSlider(...):` raises with clear message
- [ ] No new top-level dependency in `pyproject.toml`

Report status back to the user with the final commit SHA and a summary of what shipped.

---

## Self-Review Notes (post-write)

- **Spec coverage:** Tasks 1-20 walk every section of the design spec (package layout, hierarchy, lifecycle, example app, tests, acceptance criteria).
- **Markup-inlining gap:** Each concrete class ships first with a `shiny.ui.*` delegation in `tagify()` (interim), then Step 5 of those tasks instructs the implementer to inline the actual markup. This is done in two stages so the snapshot test acts as the regression net during the inlining. Tasks 9–15 each include this two-stage flow.
- **`lookup_component` open question:** Task 19 flags that the example app may want a `lookup_component(session, id)` helper. This is an implementation detail; the design spec explicitly defers "how `server()` captures component instances" to the implementation plan. Implementer chooses inline-construction vs lookup-by-id.
- **Card client wiring out of scope:** Task 15 notes that the actual client-side JS that pushes `card.full_screen` to `input.<id>()` is out of scope. The `full_screen_value()` accessor is tested by mocking the session input directly; real wire-level full-screen events require Stage B work.
- **`Serializer` import path:** Task 5 Step 3 includes a note for the implementer to verify the exact import path in the installed Shiny version. The spec is intentionally non-prescriptive on which path; minor adjustment expected.
- **`input_handler_name` for accordion:** Task 14 places a literal `"shiny.bindings.accordion"` that the implementer is instructed to verify against `shiny/_input_handler.py`. The pinning test catches drift.
