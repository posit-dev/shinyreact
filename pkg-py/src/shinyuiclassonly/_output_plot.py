"""output_plot — placement helper for plot outputs, structure-only.

Carries the configuration flags (``click``, ``dblclick``, ``hover``,
``brush``, ``inline``, ``fill``). The derived-input accessors that lived
on ``shinyui.render_plot`` are dropped — server code reads
``input.<id>_click()`` / ``input.<id>_brush()`` etc. directly.
"""

from __future__ import annotations

from htmltools import Tag
from shiny.types import MISSING, MISSING_TYPE

from ._roles import UiOutput


class output_plot(UiOutput):
    """Plot output placeholder."""

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
