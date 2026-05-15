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
