"""output_code — class-based output_code."""

from __future__ import annotations

from htmltools import Tagified

from ._roles import UiOutput


class output_code(UiOutput):
    """Verbatim-text output placeholder.

    No wire input value — this is a pure output element. The server populates
    it by decorating a function with ``@render.code`` whose name matches ``id``.

    Example
    -------
    .. code-block:: python

        summary_code = output_code("summary")

        # Placed in the UI tree:
        with accordion_panel("Diagnostics"):
            summary_code

        # In the server (Core) or at module top-level (Express):
        @render.code
        def summary():
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

    def tagify(self) -> Tagified:
        import shiny.ui as _sui

        return _sui.output_code(self.id, placeholder=self.placeholder).tagify()
