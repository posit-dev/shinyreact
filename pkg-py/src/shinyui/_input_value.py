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

from shiny.input_handler import input_handlers

from ._bookmark import register_instance


def register_input_handler(name: str, fn: Callable[..., Any]) -> None:
    """Thin wrapper so tests can monkeypatch this symbol on _input_value."""
    input_handlers.add(name)(fn)


class HasInputValue:
    input_handler_name: ClassVar[str] = ""
    _input_handler: ClassVar[Callable[..., Any] | None] = None
    bookmark_serializer: ClassVar[Any] = None  # Serializer type; Any for flexibility

    @classmethod
    def _register_input_handler(cls) -> None:
        """Idempotent. Call once at module load if this class declares a handler."""
        if cls.input_handler_name and cls._input_handler is not None:
            register_input_handler(cls.input_handler_name, cls._input_handler)

    def __init__(
        self,
        *args: Any,
        id: str,
        bookmark_serializer: Any = None,
        **kwargs: Any,
    ) -> None:
        self.id = id
        self._bookmark_serializer = (
            bookmark_serializer
            if bookmark_serializer is not None
            else type(self).bookmark_serializer
        )
        super().__init__(*args, **kwargs)
        # After super().__init__: UiComponent has set self._session.
        if self._session is not None:  # type: ignore[attr-defined]
            register_instance(self._session, id, self)  # type: ignore[arg-type]
