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

from ._ctx_stack import dispatch_to_active_parent, pop, push


class CtxTag(Tag):
    _ctx_token: contextvars.Token[tuple[Any, ...]]

    def __enter__(self) -> Self:  # type: ignore[override]
        self._ctx_token = push(self)
        return self

    def __exit__(self, *exc: object) -> None:
        pop(self._ctx_token)
        # Mirror AllowsChildren.__exit__: on normal exit, forward self to the
        # enclosing parent so nested ``with CtxTag(...)`` blocks compose into
        # the surrounding tree rather than being silently dropped.
        if exc[0] is None:
            dispatch_to_active_parent(self)
