"""UiInputActionButton — class-based input_action_button with a count accessor."""

from __future__ import annotations

from typing import Any, Optional

from htmltools import Tag, TagChild

from ._reactive import reactive_calc_method
from ._roles import UiInput
from ._updatable import Updatable

_MISSING = object()


class UiInputActionButton(UiInput, Updatable):
    """Server-readable button.

    ``input.<id>()`` is an integer counter that starts at 0 and increments on
    each click. The class accessor :meth:`clicked` returns the current value as
    a reactive read; pair with :func:`shiny.reactive.event` to run code on each
    click without firing on the initial value.
    """

    def __init__(
        self,
        id: str,
        label: TagChild,
        *,
        icon: TagChild = None,
        width: Optional[str] = None,
        disabled: bool = False,
    ) -> None:
        self.label = label
        self.icon = icon
        self.width = width
        self.disabled = disabled
        super().__init__(id=id)

    @reactive_calc_method
    def clicked(self) -> int:
        """Click counter; 0 before the first click, +1 per click."""
        return int(self._read_input() or 0)

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.input_action_button(
            self.id,
            self.label,
            icon=self.icon,
            width=self.width,
            disabled=self.disabled,
        )

    def update(
        self,
        *,
        label: TagChild = _MISSING,  # type: ignore[assignment]
        icon: TagChild = _MISSING,  # type: ignore[assignment]
        disabled: bool = _MISSING,  # type: ignore[assignment]
    ) -> None:
        """Push label / icon / disabled changes to the client."""
        import shiny.ui as _sui

        sess = self._require_session(for_op="update")
        kwargs: dict[str, Any] = {}
        if label is not _MISSING:
            kwargs["label"] = label
        if icon is not _MISSING:
            kwargs["icon"] = icon
        if disabled is not _MISSING:
            kwargs["disabled"] = disabled
        _sui.update_action_button(self.id, session=sess, **kwargs)


def input_action_button(
    id: str,
    label: TagChild,
    **kwargs: Any,
) -> UiInputActionButton:
    return UiInputActionButton(id, label, **kwargs)
