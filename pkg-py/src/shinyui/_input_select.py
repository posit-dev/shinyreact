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
    """Dropdown / multi-select input.

    Wire id: ``input.<id>()`` is the selected key string, or a ``list[str]``
    when ``multiple=True``. The class accessor :meth:`value` returns the same.

    Example
    -------
    .. code-block:: python

        c = input_select("c", "Column", {"a": "Alpha", "b": "Beta"})

        # In server:
        @render.code
        def summary():
            return f"column = {c.value()}"

        # Push a new selection from the server:
        c.update(selected="b")
    """

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
        """Build a select input.

        Parameters
        ----------
        id
            Input id; available as ``input.<id>()`` server-side, or via
            :meth:`value`.
        label
            Display label.
        choices
            Selectable options — a list/tuple of strings, a ``{value: label}``
            mapping, or a nested ``{group: {value: label}}`` mapping for
            option-group rendering.
        selected
            Initially selected value(s). ``None`` defaults to the first choice.
            Pass a list when ``multiple=True``.
        multiple
            Allow multiple simultaneous selections.
        width, size
            Forwarded verbatim to :func:`shiny.ui.input_select`; see shiny's
            docs for semantics.
        """
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
