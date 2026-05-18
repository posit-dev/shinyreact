"""input_action_button — class-based input_action_button with a value accessor.

Demonstrates the ``__init_subclass__`` registration pattern: by declaring
``input_handler_name`` and ``_input_handler`` on the class, the handler is
auto-registered with Shiny's ``input_handlers`` registry when the class is
defined. The hook lives on :class:`shinyui.HasInputValue` so every
``UiInput`` subclass benefits from it — most classes leave the defaults and
the registration is a no-op for them.

Note: the wire ``type`` attribute on shiny's action-button markup is
``"shiny.action"``, so real wire traffic is processed by the handler in
``shiny.input_handler``. Our handler is registered under ``"shinyui.action"``
and serves the demo purpose only — proves ``__init_subclass__`` does fire,
without colliding with shiny's built-in.
"""

from __future__ import annotations

from typing import Any, Optional

from htmltools import Tag, TagChild

from ._reactive import reactive_calc_method
from ._roles import UiInput
from ._updatable import Updatable

_MISSING = object()


class input_action_button(UiInput, Updatable):
    """Server-readable action button.

    Wire id: ``input.<id>()`` is an integer click counter that starts at ``0``
    and increments on each click. The class accessor :meth:`value` returns
    the same value as a reactive read.

    Pair :meth:`value` with :func:`shiny.reactive.event` and
    ``ignore_init=True`` to respond only to real clicks, not the initial
    ``0`` value registered at page load.

    Example
    -------
    .. code-block:: python

        go = input_action_button("go", "Run")

        # In server:
        @reactive.event(go.value, ignore_init=True)
        def _on_click():
            ...

        # Push label / disabled state from the server:
        go.update(label="Running...", disabled=True)
    """

    # Auto-registered via HasInputValue.__init_subclass__ when this class
    # body finishes executing. See the module docstring for the trade-off.
    input_handler_name = "shinyui.action"

    @staticmethod
    def _input_handler(value: Any, name: Any, session: Any) -> int:
        """Coerce wire value to a plain int.

        (shiny's built-in handler returns an ActionButtonValue; we keep it
        simpler here since the demo doesn't actually receive wire traffic.)
        """
        return int(value or 0)

    def __init__(
        self,
        id: str,
        label: TagChild,
        *,
        icon: TagChild = None,
        width: Optional[str] = None,
        disabled: bool = False,
    ) -> None:
        """Build an action button.

        Parameters
        ----------
        id
            Input id; available as ``input.<id>()`` server-side, or via
            :meth:`value`.
        label
            Button label text (or any ``TagChild``).
        icon
            Optional icon to display before the label.
        width, disabled
            Forwarded verbatim to :func:`shiny.ui.input_action_button`; see
            shiny's docs for semantics.
        """
        self.label = label
        self.icon = icon
        self.width = width
        self.disabled = disabled
        super().__init__(id=id)

    @reactive_calc_method
    def value(self) -> int:
        """Click counter; ``0`` before the first click, ``+1`` per click."""
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
