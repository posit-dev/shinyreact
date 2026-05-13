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

from typing import Any

from htmltools import TagChild
from typing_extensions import Self


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
