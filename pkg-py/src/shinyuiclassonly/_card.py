"""card — layout container.

Structure-only sibling of ``shinyui.card``. Same Express + Core overloads,
same ``tagify()`` delegation to ``shiny.ui.card``. The session-aware
``value_full_screen()`` reader and ``update()`` are dropped. ``id`` is
optional (no accessor needs it).
"""

from __future__ import annotations

from typing import Any, Optional, overload

from htmltools import TagChild, Tagified

from ._children import AllowsChildren
from ._roles import UiLayout


class card(UiLayout, AllowsChildren):
    """Card container with optional full-screen toggle.

    No server-side accessor here. Read the full-screen state via
    ``input.<id>_full_screen()`` on the server side (shiny's card binding
    pushes that input id when ``id=`` is supplied).
    """

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
    @overload
    def __init__(
        self,
        *,
        id: Optional[str] = None,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None: ...

    # Core overload — inline positional children.
    @overload
    def __init__(
        self,
        *args: TagChild,
        id: Optional[str] = None,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None: ...

    def __init__(
        self,
        *args: TagChild,
        id: Optional[str] = None,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None:
        self.id = id
        self._full_screen = full_screen
        self.height = height
        self.max_height = max_height
        self.min_height = min_height
        self.fill = fill
        self.class_ = class_
        super().__init__(*args)

    def tagify(self) -> Tagified:
        import shiny.ui as _sui

        kwargs: dict[str, Any] = {
            "full_screen": self._full_screen,
            "fill": self.fill,
        }
        if self.id is not None:
            kwargs["id"] = self.id
        if self.height is not None:
            kwargs["height"] = self.height
        if self.max_height is not None:
            kwargs["max_height"] = self.max_height
        if self.min_height is not None:
            kwargs["min_height"] = self.min_height
        if self.class_ is not None:
            kwargs["class_"] = self.class_

        return _sui.card(*self.children, **kwargs).tagify()
