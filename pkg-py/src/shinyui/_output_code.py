"""output_code — class-based output_code."""

from __future__ import annotations

from typing import Any, Callable

from htmltools import Tag

from ._roles import UiOutput


class output_code(UiOutput):
    """Verbatim-text output placeholder.

    No wire input value — this is a pure output element. The server populates
    it by decorating a function with ``@render.code`` whose name matches ``id``,
    or via the :meth:`render` instance method.

    Example
    -------
    .. code-block:: python

        summary_code = output_code("summary")

        # Placed in the UI tree:
        with accordion_panel("Diagnostics"):
            summary_code

        # In the server (or at module top-level in Express):
        @summary_code.render
        def _():
            return f"n = {n.value()}"
    """

    def __init__(self, id: str, *, placeholder: bool = True) -> None:
        """Build a verbatim-text output.

        Parameters
        ----------
        id
            Output id; must match a ``@render.code``-decorated function in the
            server.
        placeholder
            Show a placeholder block in the UI before the server renders.
            Forwarded to :func:`shiny.ui.output_code`.
        """
        self.id = id
        self.placeholder = placeholder
        super().__init__()

    def render(self, fn: Callable[..., Any]) -> Any:
        """Bind ``fn`` as the renderer for this output instance.

        Returns the wrapped :class:`shiny.render.code` renderer. The function
        is registered with Shiny under ``self.id``, regardless of its own
        ``__name__``. Use as a decorator:

        .. code-block:: python

            out = output_code("summary")

            @out.render
            def _():
                return "..."

        In Shiny Express, this avoids the auto-display behaviour of plain
        ``@render.code`` — UI placement is determined by where *this* instance
        is placed in the UI tree, not by where the renderer decorator appears.
        """
        from shiny import render as _r

        fn.__name__ = self.id
        return _r.code(fn)

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.output_code(self.id, placeholder=self.placeholder)
