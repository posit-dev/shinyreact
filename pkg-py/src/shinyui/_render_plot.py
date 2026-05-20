"""render_plot — plot renderer with shinyui-side placeholder + derived-input accessors.

Inherits from shiny.render.plot for the actual rendering. Overrides
auto_output_ui() to emit a shinyui output_plot (which still ultimately
delegates to shiny.ui.output_plot, but goes through our class). Adds typed
accessors for the four derived input ids:

  ===================  ============================================
  Wire id              Accessor (reactive read)
  ===================  ============================================
  input.<id>_click     :meth:`value_click`
  input.<id>_dblclick  :meth:`value_dbl`
  input.<id>_hover     :meth:`value_hover`
  input.<id>_brush     :meth:`value_brush`
  ===================  ============================================

Interaction flags (click=, dblclick=, hover=, brush=, inline=, fill=) live on
the renderer rather than as parameters to a separate output_plot placeholder.
In Express, ``@render_plot(click=True, ...)`` is enough — the renderer auto-
places itself with the right flags. In Core, the user still constructs
``output_plot("id", click=True, ...)`` in app_ui for placement; the renderer
in the server reads the derived inputs via its own accessors.
"""

from __future__ import annotations

from typing import Any, Optional

from htmltools import Tag
from shiny.render._render import plot as _shiny_plot
from shiny.session import require_active_session
from shiny.types import MISSING, MISSING_TYPE

from ._reactive import reactive_calc_method


class render_plot(_shiny_plot):
    """Plot renderer with shinyui-side placeholder + derived-input accessors.

    Inherits from :class:`shiny.render.plot` for the actual rendering. Adds:

    - Interaction flags (``click``, ``dblclick``, ``hover``, ``brush``,
      ``inline``, ``fill``) carried on the renderer.
    - Typed accessors for the four derived input ids that the shiny plot
      binding pushes: :meth:`value_click`, :meth:`value_dbl`,
      :meth:`value_hover`, :meth:`value_brush`.
    - An overridden :meth:`auto_output_ui` that emits a
      :class:`shinyui.output_plot` configured with the same flags — so in
      Express, ``@render_plot(click=True)`` is enough for both server logic
      and UI placement.

    In Core, construct an ``output_plot("id", click=True, ...)`` in ``app_ui``
    for placement; in ``server``, use ``@render_plot(click=True, ...)`` and
    read derived inputs via the accessors.
    """

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

    def auto_output_ui(self, **_kw: object) -> Tag:
        from ._output_plot import output_plot

        return output_plot(
            self.output_id,
            inline=self.inline,
            click=self.click_enabled,
            dblclick=self.dblclick_enabled,
            hover=self.hover_enabled,
            brush=self.brush_enabled,
            fill=self.fill,
        ).tagify()

    @reactive_calc_method
    def value_click(self) -> Any:
        return self._read_derived("_click")

    @reactive_calc_method
    def value_dbl(self) -> Any:
        return self._read_derived("_dblclick")

    @reactive_calc_method
    def value_hover(self) -> Any:
        return self._read_derived("_hover")

    @reactive_calc_method
    def value_brush(self) -> Any:
        return self._read_derived("_brush")

    def _read_derived(self, suffix: str) -> Any:
        sess = require_active_session(None)
        return sess.input[f"{self.output_id}{suffix}"]()
