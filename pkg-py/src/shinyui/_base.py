"""UiComponent — abstract base for the shinyui class hierarchy.

Single source of truth for:
  - `self._session`: the active session captured at construction (may be None)
  - `_require_session(for_op=...)`: resolves a session at call time. If a
    session was captured at construction, use it; otherwise fall back to the
    **root scope** of the currently-active session. Raises ``RuntimeError`` if
    no session is reachable.
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
from typing import Any

from htmltools import Tagified
from shiny.session import Session, get_current_session


class UiComponent(ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Capture session BEFORE super() so mixins can read self._session
        # in their own __init__ after they call super().__init__(**kw).
        # Forward *args cooperatively so AllowsChildren (next in MRO when the
        # class is declared as MyComp(UiComponent, AllowsChildren)) receives
        # positional children arguments.
        #
        # Why capture at construction even when the session may be None:
        # in Shiny Express, ``app.py`` is re-run once per session inside that
        # session's context, so ``get_current_session()`` returns the active
        # session here and we keep a direct reference to it for the lifetime
        # of this instance. In Shiny Core, the module body runs once at
        # process startup (no session bound), so this captures ``None`` and
        # ``_require_session`` falls back to the active root session at
        # call time. See ``_require_session`` for the unification logic.
        self._session: Session | None = get_current_session()
        super().__init__(*args, **kwargs)

    def _require_session(self, *, for_op: str) -> Session:
        # The Core / Express unification point.
        #
        # In **Express**, ``self._session`` was captured at __init__ time
        # because Express re-runs the app body per session. The captured
        # value is the live per-session Session — return it directly.
        #
        # In **Core**, the component was constructed at module top level
        # with no session bound (``self._session is None``). Reads happen
        # later, inside ``server(input, output, session)`` — at which point
        # a session is active for the current request. Look it up via
        # ``get_current_session()`` and step up to ``.root_scope()`` so we
        # always resolve against the top-level (un-namespaced) session,
        # regardless of whether the read happens inside a ``@module``
        # scope. shinyui component ids are not namespaced, so the root
        # session is the correct lookup target.
        #
        # This two-layer lookup is what lets a single ``input_slider(...)``
        # instance work in both Core (module top-level + ``server``) and
        # Express (per-session app body) without any per-component opt-in.
        sess: Session | None = self._session
        if sess is None:
            current = get_current_session()
            if current is not None:
                sess = current.root_scope()
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
    def tagify(self) -> Tagified: ...
