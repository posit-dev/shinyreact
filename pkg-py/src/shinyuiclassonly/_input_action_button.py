"""input_action_button — class-based action button, structure-only.

Structure-only sibling of ``shinyui.input_action_button``. The class-level
``input_handler_name`` and ``__init_subclass__`` registration are dropped
along with all of ``HasInputValue`` (see the spec). Server code reads the
click counter via ``input.<id>()`` directly.
"""

from __future__ import annotations

from typing import Optional

from htmltools import Tag, TagChild

from ._roles import UiInput


class input_action_button(UiInput):
    """Server-readable action button.

    Wire id: ``input.<id>()`` is an integer click counter starting at 0,
    incremented on each click. There is no class-side accessor.
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
        self.id = id
        self.label = label
        self.icon = icon
        self.width = width
        self.disabled = disabled

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        return _sui.input_action_button(
            self.id,
            self.label,
            icon=self.icon,
            width=self.width,
            disabled=self.disabled,
        )
