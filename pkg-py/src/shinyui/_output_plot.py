"""UiOutputPlot — output with read-only client-side interaction signals.

Derived input ids (the four that ``shiny.ui.output_plot`` actually pushes):

  ===================  ============================================
  Wire id              Accessor (reactive read)
  ===================  ============================================
  input.<id>_click     :meth:`UiOutputPlot.click_value`
  input.<id>_dblclick  :meth:`UiOutputPlot.dbl_value`
  input.<id>_hover     :meth:`UiOutputPlot.hover_value`
  input.<id>_brush     :meth:`UiOutputPlot.brush_value`
  ===================  ============================================

No HasInputValue, no Updatable. Derived inputs flow through Shiny's
auto-created Value[Any] mechanism on first ``session.input[...]`` access.

Two interactions that shinyui does NOT expose because the shiny binding
does not push them: ``_limits`` (zoom bounds) and ``_selection`` (lasso /
selected-points). If shiny grows those signals upstream, add the matching
``limits_value`` / ``selection_value`` accessors here.
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
    def dbl_value(self) -> Any:
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
