"""accordion_panel — layout child of accordion.

Structure-only sibling of ``shinyui.accordion_panel``. Same Express + Core
overloads, same ``tagify()`` delegation. Has no wire id of its own.
"""

from __future__ import annotations

from typing import overload

from htmltools import TagChild, Tagified
from shiny.types import MISSING, MISSING_TYPE

from ._children import AllowsChildren
from ._roles import UiLayout


class accordion_panel(UiLayout, AllowsChildren):
    """A single collapsible panel within an :class:`accordion`."""

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
    @overload
    def __init__(
        self,
        title: str,
        *,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None: ...

    # Core overload — inline positional children.
    @overload
    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None: ...

    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None:
        self.title = title
        self._value: str | MISSING_TYPE = value
        self.icon = icon
        super().__init__(*args)

    @property
    def value(self) -> str:
        if isinstance(self._value, MISSING_TYPE):
            return self.title
        return self._value

    def tagify(self) -> Tagified:
        # shiny.ui.accordion does isinstance(panel, AccordionPanel) and
        # rejects pre-rendered Tags, so for standalone .tagify() we stamp
        # a placeholder _accordion_id keyed off the panel's value. The
        # parent :class:`accordion` builds its own AccordionPanel wrappers
        # from this instance's attributes (it can't reuse the rendered
        # Tag).
        import shiny.ui as _sui

        panel = _sui.accordion_panel(
            self.title,
            *self.children,
            value=self._value,
            icon=self.icon,
        )
        panel._accordion_id = f"_orphan_{self.value}"
        return panel.tagify()
