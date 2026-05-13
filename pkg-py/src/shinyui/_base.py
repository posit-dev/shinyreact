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
from typing import Any, ClassVar

from htmltools import HTMLDependency, Tag
from shiny.session import Session, get_current_session
from typing_extensions import Self


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

    def __enter__(self) -> Self:
        # AllowsChildren overrides __enter__ to return self.  When the MRO
        # places UiComponent before AllowsChildren (the typical mixin order),
        # we must explicitly delegate so the mixin wins.
        from shinyui._children import AllowsChildren  # local import avoids circular

        if isinstance(self, AllowsChildren):
            return AllowsChildren.__enter__(self)  # type: ignore[return-value]
        raise TypeError(
            f"{type(self).__name__} does not accept children; "
            f"only components declaring `AllowsChildren` may be used as `with` blocks."
        )

    def __exit__(self, *exc: object) -> None:
        return None
