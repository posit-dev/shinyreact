"""input_select — class-based input_select."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union

from htmltools import Tag, TagChild

from ._reactive import reactive_calc_method
from ._roles import UiInput
from ._updatable import Updatable

_MISSING = object()

_Choices = Mapping[str, str]
_OptGrpChoices = Mapping[str, _Choices]
SelectChoicesArg = Union[
    "list[str]",
    "tuple[str, ...]",
    _Choices,
    _OptGrpChoices,
]


class input_select(UiInput, Updatable):  # noqa: N801
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
        self.label = label
        self.choices = choices
        self._init_selected = selected
        self.multiple = multiple
        self.width = width
        self.size = size
        super().__init__(id=id)

    @reactive_calc_method
    def value(self) -> Any:
        return self._read_input()

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.input_select(
            self.id,
            self.label,
            self.choices,
            selected=self._init_selected,
            multiple=self.multiple,
            width=self.width,
            size=self.size,
        )

    def update(
        self,
        *,
        label: TagChild = _MISSING,  # type: ignore[assignment]
        choices: SelectChoicesArg = _MISSING,  # type: ignore[assignment]
        selected: Optional[str | list[str]] = _MISSING,  # type: ignore[assignment]
    ) -> None:
        import shiny.ui as _sui

        sess = self._require_session(for_op="update")
        kwargs: dict[str, Any] = {}
        if label is not _MISSING:
            kwargs["label"] = label
        if choices is not _MISSING:
            kwargs["choices"] = choices
        if selected is not _MISSING:
            kwargs["selected"] = selected
        _sui.update_select(self.id, session=sess, **kwargs)
