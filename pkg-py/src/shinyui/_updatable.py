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
