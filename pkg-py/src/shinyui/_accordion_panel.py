"""UiAccordionPanel — layout child of UiAccordion."""

from __future__ import annotations

from typing import Any

from htmltools import TagChild
from shiny.types import MISSING, MISSING_TYPE
from shiny.ui._accordion import AccordionPanel

from ._children import AllowsChildren
from ._roles import UiLayout


class UiAccordionPanel(UiLayout, AllowsChildren):
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


def accordion_panel(title: str, *args: TagChild, **kwargs: Any) -> UiAccordionPanel:
    return UiAccordionPanel(title, *args, **kwargs)
