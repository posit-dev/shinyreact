"""output_plot — placement helper for plot outputs.

This class is now a pure placement helper. It carries the configuration
flags (``click``, ``dblclick``, ``hover``, ``brush``, ``inline``, ``fill``)
that Core needs at ``app_ui`` time — before any renderer exists — and
delegates to :func:`shiny.ui.output_plot` in :meth:`tagify`.

Derived-input accessors (``value_click``, ``value_dbl``, ``value_hover``,
``value_brush``) live on :class:`shinyui.render_plot`, which is the
renderer side of the same plot output. The renderer owns the session at
read time in both Core and Express, so it's the natural home for those
accessors.

See :class:`shinyui.render_plot` for the accessor surface.

Two interactions that shinyui does NOT expose because the shiny binding
does not push them: ``_limits`` (zoom bounds) and ``_selection`` (lasso /
selected-points). If shiny grows those signals upstream, add the matching
``value_limits`` / ``value_selection`` accessors on ``render_plot``.
"""

from __future__ import annotations

from htmltools import Tagified
from shiny.types import MISSING, MISSING_TYPE

from ._roles import UiOutput


class output_plot(UiOutput):
    """Plot output placeholder.

    Pure placement helper — carries the interaction configuration flags that
    Core needs at ``app_ui`` time. In Express, the matching
    :class:`shinyui.render_plot` auto-places its own placeholder via
    ``auto_output_ui()`` and you typically don't construct ``output_plot``
    directly.

    Example
    -------
    .. code-block:: python

        # Core (app.py with positional composition)
        p = output_plot("plot", click=True, brush=True)

        # In server:
        @su.render_plot(click=True, brush=True)
        def plot():
            ...

        @render.code
        def diag():
            return f"click = {plot.value_click()}\\nbrush = {plot.value_brush()}\\n"
    """

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
        """Build a plot output placeholder.

        Parameters
        ----------
        id
            Output id; must match a ``@render.plot``- or
            ``@shinyui.render_plot``-decorated function in the server.
        width, height
            CSS dimensions of the plot container.
        click, dblclick, hover, brush
            Enable the matching client-side interaction. Reads happen on
            the matching :class:`shinyui.render_plot` instance, not here.
        inline, fill
            Forwarded verbatim to :func:`shiny.ui.output_plot`; see shiny's
            docs for semantics.
        """
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

    def tagify(self) -> Tagified:
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
        ).tagify()
