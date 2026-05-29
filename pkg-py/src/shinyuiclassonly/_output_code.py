"""output_code — class-based verbatim-text output, structure-only."""

from __future__ import annotations

from htmltools import Tagified

from ._roles import UiOutput


class output_code(UiOutput):
    """Verbatim-text output placeholder.

    No wire input value — pure output. The server populates it by
    decorating a function with ``@render.code`` whose name matches ``id``.
    """

    def __init__(self, id: str, *, placeholder: bool = True) -> None:
        self.id = id
        self.placeholder = placeholder

    def tagify(self) -> Tagified:
        import shiny.ui as _sui

        return _sui.output_code(self.id, placeholder=self.placeholder).tagify()
