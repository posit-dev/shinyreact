"""CtxTag — ``htmltools.Tag`` subclass with contextvar-aware ``__enter__``.

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
