"""output_plot — output with read-only client-side interaction signals.

Derived input ids (the four that ``shiny.ui.output_plot`` actually pushes):

  ===================  ============================================
  Wire id              Accessor (reactive read)
  ===================  ============================================
  input.<id>_click     :meth:`output_plot.click_value`
  input.<id>_dblclick  :meth:`output_plot.dbl_value`
  input.<id>_hover     :meth:`output_plot.hover_value`
  input.<id>_brush     :meth:`output_plot.brush_value`
  ===================  ============================================

No HasInputValue, no Updatable. Derived inputs flow through Shiny's
auto-created Value[Any] mechanism on first ``session.input[...]`` access.

Two interactions that shinyui does NOT expose because the shiny binding
does not push them: ``_limits`` (zoom bounds) and ``_selection`` (lasso /
selected-points). If shiny grows those signals upstream, add the matching
``limits_value`` / ``selection_value`` accessors here.
"""

from __future__ import annotations

from typing import Any, Callable

from htmltools import Tag
from shiny.types import MISSING, MISSING_TYPE

from ._reactive import reactive_calc_method
from ._roles import UiOutput


class output_plot(UiOutput):
    """Plot output with optional client-side interaction signals.

    No primary ``input.<id>()`` value. When interaction flags are enabled,
    the browser pushes derived wire ids that are accessible via class
    accessors:

    =====================  ======================================
    Wire id                Accessor
    =====================  ======================================
    ``input.<id>_click``   :meth:`click_value`
    ``input.<id>_dblclick`` :meth:`dbl_value`
    ``input.<id>_hover``   :meth:`hover_value`
    ``input.<id>_brush``   :meth:`brush_value`
    =====================  ======================================

    Example
    -------
    .. code-block:: python

        p = output_plot("plot", click=True, brush=True)

        # In server:
        @reactive.effect
        def _():
            coords = p.click_value()
            if coords:
                print(coords["x"], coords["y"])
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
        """Build a plot output.

        Parameters
        ----------
        id
            Output id; must match a ``@render.plot``-decorated function in the
            server.
        width, height
            CSS dimensions of the plot container.
        click
            Enable click interaction; read via :meth:`click_value`.
        dblclick
            Enable double-click interaction; read via :meth:`dbl_value`.
        hover
            Enable hover interaction; read via :meth:`hover_value`.
        brush
            Enable brush (drag-select) interaction; read via :meth:`brush_value`.
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

    def render(self, fn: Callable[..., Any]) -> Any:
        """Bind ``fn`` as the plot renderer for this output instance.

        Returns the wrapped :class:`shiny.render.plot` renderer. The function
        is registered with Shiny under ``self.id``, regardless of its own
        ``__name__``. See :meth:`output_code.render` for the full rationale.

        .. code-block:: python

            plot_handle = output_plot("plot", click=True, brush=True)

            @plot_handle.render
            def _():
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots()
                ax.plot([1, 2, 3])
                return fig
        """
        from shiny import render as _r

        fn.__name__ = self.id
        return _r.plot(fn)

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
