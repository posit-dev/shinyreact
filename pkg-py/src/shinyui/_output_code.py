"""output_code — class-based output_code."""

from __future__ import annotations

from htmltools import Tag

from ._roles import UiOutput


class output_code(UiOutput):
    """Verbatim-text output placeholder.

    No wire input value — this is a pure output element. The server populates
    it by decorating a function with ``@render.code`` whose name matches ``id``.

    Example
    -------
    .. code-block:: python

        output_code("summary")

        # In server:
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

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.output_code(self.id, placeholder=self.placeholder)
