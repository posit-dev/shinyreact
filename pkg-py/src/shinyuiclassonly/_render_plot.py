"""render_plot — shiny.render.plot subclass carrying interaction flags.

Structure-only sibling of ``shinyui.render_plot``. Keeps:

  - the interaction flags (``click``, ``dblclick``, ``hover``, ``brush``,
    ``inline``, ``fill``) carried on the renderer
  - the ``auto_output_ui()`` override that emits a
    :class:`shinyuiclassonly.output_plot` so Express's auto-placement
    produces a properly-configured placeholder

Drops the session-bound ``.click_value()`` / ``.dbl_value()`` /
``.hover_value()`` / ``.brush_value()`` accessors — read
``input.<id>_click()`` / ``input.<id>_brush()`` etc. directly from the
server.

Note: ``auto_output_ui()`` returns the ``output_plot`` instance directly
(not ``.tagify()``'d). htmltools' walker tagifies it later. This
reinforces the "components are Tagifiable, not Tag" lesson — and differs
from ``shinyui.render_plot``, which returns a Tag because its
``auto_output_ui`` is typed ``-> Tag``.
"""

from __future__ import annotations

from typing import Any, Optional

from shiny.render._render import plot as _shiny_plot
from shiny.types import MISSING, MISSING_TYPE


class render_plot(_shiny_plot):
    """Plot renderer that auto-places a :class:`output_plot` placeholder."""

    def __init__(
        self,
        _fn: Any = None,
        *,
        alt: Optional[str] = None,
        width: float | None | MISSING_TYPE = MISSING,
        height: float | None | MISSING_TYPE = MISSING,
        inline: bool = False,
        click: bool = False,
        dblclick: bool = False,
        hover: bool = False,
        brush: bool = False,
        fill: bool | MISSING_TYPE = MISSING,
        **kwargs: object,
    ) -> None:
        super().__init__(_fn, alt=alt, width=width, height=height, **kwargs)
        self.inline = inline
        self.click_enabled = click
        self.dblclick_enabled = dblclick
        self.hover_enabled = hover
        self.brush_enabled = brush
        self.fill = fill

    def auto_output_ui(self, **_kw: object):  # type: ignore[override]
        from ._output_plot import output_plot

        return output_plot(
            self.output_id,
            inline=self.inline,
            click=self.click_enabled,
            dblclick=self.dblclick_enabled,
            hover=self.hover_enabled,
            brush=self.brush_enabled,
            fill=self.fill,
        )
