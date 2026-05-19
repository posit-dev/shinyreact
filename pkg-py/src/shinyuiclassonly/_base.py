"""UiComponent — abstract base for the shinyuiclassonly class hierarchy.

This is the structure-only sibling of ``shinyui.UiComponent``. It carries
only the bits that affect the class hierarchy:

  - ``html_dependencies`` ClassVar (default ``()``)
  - abstract :meth:`tagify` returning a ``Tag``

Deliberately omitted (the "no session" delta vs. ``shinyui``):

  - no ``_session`` attribute captured in ``__init__``
  - no ``_require_session(for_op=...)``
  - no ``_read_input(suffix="")``

Context-manager protocol (``__enter__`` / ``__exit__``) is declared only
on :class:`shinyuiclassonly.AllowsChildren`. Subclasses that don't inherit
``AllowsChildren`` will raise a TypeError if used as ``with ...:``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from htmltools import HTMLDependency, Tag


class UiComponent(ABC):
    html_dependencies: ClassVar[tuple[HTMLDependency, ...]] = ()

    @abstractmethod
    def tagify(self) -> Tag: ...
