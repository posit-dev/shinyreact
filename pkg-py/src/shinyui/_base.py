"""UiComponent — abstract base for the shinyui class hierarchy.

Single source of truth for:
  - `self._session`: the active session captured at construction (may be None)
  - `_require_session(for_op=...)`: resolves a session at call time, with a fallback
    to the current session, raising RuntimeError if none is reachable.
  - `_read_input(suffix="")`: reads `session.input[f"{self.id}{suffix}"]()`.

`tagify()` is abstract. Context-manager protocol (``__enter__``/``__exit__``) is
declared only on :class:`shinyui.AllowsChildren`, so type checkers immediately
flag ``with input_slider(...):`` and similar misuses — `input_slider` does not
declare ``__enter__`` because it doesn't inherit ``AllowsChildren``.

Container subclasses should end their `tagify()` with `.tagify()` on the result —
htmltools' walker iterates Tagifiable→Tagifiable chains during that single call,
so calling it once on the outer tag fully resolves our Tagifiable descendants.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from htmltools import HTMLDependency, Tag
from shiny.session import Session, get_current_session


class UiComponent(ABC):
    html_dependencies: ClassVar[tuple[HTMLDependency, ...]] = ()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Capture session BEFORE super() so mixins can read self._session
        # in their own __init__ after they call super().__init__(**kw).
        # Forward *args cooperatively so AllowsChildren (next in MRO when the
        # class is declared as MyComp(UiComponent, AllowsChildren)) receives
        # positional children arguments.
        self._session: Session | None = get_current_session()
        super().__init__(*args, **kwargs)

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
