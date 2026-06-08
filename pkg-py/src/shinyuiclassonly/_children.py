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
