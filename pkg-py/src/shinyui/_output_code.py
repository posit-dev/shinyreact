"""UiOutputCode — class-based output_code."""

from __future__ import annotations

from htmltools import Tag

from ._roles import UiOutput


class UiOutputCode(UiOutput):
    def __init__(self, id: str, *, placeholder: bool = True) -> None:
        self.id = id
        self.placeholder = placeholder
        super().__init__()

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.output_code(self.id, placeholder=self.placeholder)


def output_code(id: str, *, placeholder: bool = True) -> UiOutputCode:
    return UiOutputCode(id, placeholder=placeholder)
