"""UiOutputPlot — output with read-only client-side interaction signals.

Derived input ids:
  input.<id>_click       — {x, y} | None
  input.<id>_dblclick    — {x, y} | None
  input.<id>_hover       — {x, y} | None
  input.<id>_brush       — {xmin, xmax, ymin, ymax, ...} | None

No HasInputValue, no Updatable. Derived inputs flow through Shiny's
auto-created Value[Any] mechanism on first session.input[...] access.
"""

from __future__ import annotations

from typing import Any

from htmltools import Tag
from shiny.types import MISSING, MISSING_TYPE

from ._reactive import reactive_calc_method
from ._roles import UiOutput


class UiOutputPlot(UiOutput):
    def __init__(
        self,
        id: str,
        *,
        width: str | float | int = "100%",
        height: str | float | int = "400px",
        inline: bool = False,
        click: bool = False,
        dblclick: bool = False,
        hover: bool = False,
        brush: bool = False,
        fill: bool | MISSING_TYPE = MISSING,
    ) -> None:
        self.id = id
        self.width = width
        self.height = height
        self.inline = inline
        self.click_enabled = click
        self.dblclick_enabled = dblclick
        self.hover_enabled = hover
        self.brush_enabled = brush
        self.fill = fill
        super().__init__()

    @reactive_calc_method
    def click_value(self) -> Any:
        return self._read_input("_click")

    @reactive_calc_method
    def dblclick_value(self) -> Any:
        return self._read_input("_dblclick")

    @reactive_calc_method
    def hover_value(self) -> Any:
        return self._read_input("_hover")

    @reactive_calc_method
    def brush_value(self) -> Any:
        return self._read_input("_brush")

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.output_plot(
            self.id,
            self.width,
            self.height,
            inline=self.inline,
            click=self.click_enabled,
            dblclick=self.dblclick_enabled,
            hover=self.hover_enabled,
            brush=self.brush_enabled,
            fill=self.fill,
        )


def output_plot(id: str, **kwargs: Any) -> UiOutputPlot:
    return UiOutputPlot(id, **kwargs)
