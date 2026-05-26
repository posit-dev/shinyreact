"""input_select — class-based dropdown / multi-select, structure-only."""

from __future__ import annotations

from typing import Mapping, Optional, Union

from htmltools import TagChild, Tagified

from ._roles import UiInput

_Choices = Mapping[str, str]
_OptGrpChoices = Mapping[str, _Choices]
SelectChoicesArg = Union[
    "list[str]",
    "tuple[str, ...]",
    _Choices,
    _OptGrpChoices,
]


class input_select(UiInput):
    """Dropdown / multi-select input."""

    def __init__(
        self,
        id: str,
        label: TagChild,
        choices: SelectChoicesArg,
        *,
        selected: Optional[str | list[str]] = None,
        multiple: bool = False,
        width: Optional[str] = None,
        size: Optional[str] = None,
    ) -> None:
        self.id = id
        self.label = label
        self.choices = choices
        self._init_selected = selected
        self.multiple = multiple
        self.width = width
        self.size = size

    def tagify(self) -> Tagified:
        import shiny.ui as _sui

        return _sui.input_select(
            self.id,
            self.label,
            self.choices,
            selected=self._init_selected,
            multiple=self.multiple,
            width=self.width,
            size=self.size,
        ).tagify()
