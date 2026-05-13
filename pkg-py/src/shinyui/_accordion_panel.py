"""accordion_panel — layout child of accordion."""

from __future__ import annotations

from typing import overload

from htmltools import TagChild
from shiny.types import MISSING, MISSING_TYPE
from shiny.ui._accordion import AccordionPanel

from ._children import AllowsChildren
from ._roles import UiLayout


class accordion_panel(UiLayout, AllowsChildren):  # noqa: N801
    # Express overload: `with accordion_panel("Settings"): input_slider(...)`.
    @overload
    def __init__(
        self,
        title: str,
        *,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None: ...

    # Core overload: `accordion_panel("Settings", input_slider(...), ...)`.
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

    def tagify(self) -> AccordionPanel:  # type: ignore[override]
        import shiny.ui as _sui

        return _sui.accordion_panel(
            self.title,
            *self.children,
            value=self._value,
            icon=self.icon,
        )
