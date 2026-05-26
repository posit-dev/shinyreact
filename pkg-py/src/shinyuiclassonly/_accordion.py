"""accordion — layout with collapsible panels.

Structure-only sibling of ``shinyui.accordion``. Same Express + Core
overloads, same ``tagify()`` strategy (rebuild ``shiny.ui.accordion_panel``
wrappers inline because ``shiny.ui.accordion`` does an
``isinstance(panel, AccordionPanel)`` check on its positional args).
``open_panels()`` and ``update()`` are dropped.
"""

from __future__ import annotations

from typing import Optional, cast, overload

from htmltools import TagChild, Tagified
from typing_extensions import Self

from ._accordion_panel import accordion_panel
from ._children import AllowsChildren
from ._roles import UiLayout


def _check_panel(child: object) -> None:
    if not isinstance(child, accordion_panel):
        raise TypeError(
            f"accordion children must be accordion_panel instances, "
            f"got {type(child).__name__}"
        )


class accordion(UiLayout, AllowsChildren):
    """Accordion container with collapsible panels.

    No server-side accessor here. Read the open-panel list via
    ``input.<id>()`` and push updates via ``shiny.ui.update_accordion``
    / ``shiny.ui.update_accordion_panel``.
    """

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
    @overload
    def __init__(
        self,
        *,
        id: Optional[str] = None,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None: ...

    # Core overload — inline positional :class:`accordion_panel` instances.
    @overload
    def __init__(
        self,
        *args: accordion_panel,
        id: Optional[str] = None,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None: ...

    def __init__(
        self,
        *args: accordion_panel,
        id: Optional[str] = None,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None:
        for child in args:
            _check_panel(child)
        self.id = id
        self._open = open
        self.multiple = multiple
        self.class_ = class_
        self.width = width
        self.height = height
        super().__init__(*args)

    def append(self, child: TagChild) -> Self:
        _check_panel(child)
        return super().append(child)

    def tagify(self) -> Tagified:
        import shiny.ui as _sui

        # shiny.ui.accordion rejects pre-rendered Tags (isinstance check on
        # AccordionPanel). Rebuild wrappers from each child's stored state.
        for child in self.children:
            _check_panel(child)

        # `cast` because pyright doesn't propagate the narrowing from the
        # validation loop above into the comprehension's iteration variable.
        panels = [
            _sui.accordion_panel(
                child.title,
                *child.children,
                value=child._value,
                icon=child.icon,
            )
            for child in cast("list[accordion_panel]", self.children)
        ]
        return _sui.accordion(
            *panels,
            id=self.id,
            open=self._open,
            multiple=self.multiple,
            class_=self.class_,
            width=self.width,
            height=self.height,
        ).tagify()
