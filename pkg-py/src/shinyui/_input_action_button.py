"""UiInputActionButton — class-based input_action_button with a clicked accessor.

Also serves as the prototype's one **`__init_subclass__` demo**. Most shinyui
classes register their input handler via an explicit
``cls._register_input_handler()`` call at module load. This file uses the
alternative approach: a small ``_InputHandlerAutoRegister`` mixin whose
``__init_subclass__`` hook calls ``_register_input_handler`` automatically when
a subclass is defined — exactly the magic the umbrella spec normally avoids,
included here so the trade-off can be evaluated against the explicit pattern
side-by-side.

Note: the wire ``type`` attribute on shiny's action-button markup is
``"shiny.action"``, so the *registered-for-real-wire-traffic* handler is the
one in ``shiny.input_handler``. Our handler is registered under
``"shinyui.action"`` and serves the demo purpose only — proves the
``__init_subclass__`` mechanism does fire, without colliding with shiny's
built-in.
"""

from __future__ import annotations

from typing import Any, Optional

from htmltools import Tag, TagChild

from ._input_value import HasInputValue
from ._reactive import reactive_calc_method
from ._roles import UiInput
from ._updatable import Updatable

_MISSING = object()


class _InputHandlerAutoRegister:
    """Mixin: subclasses fire ``_register_input_handler()`` at class-def time.

    Alternative to the default explicit ``cls._register_input_handler()`` line
    used elsewhere in shinyui. Lives here as a single-class demo of the
    ``__init_subclass__`` pattern — see the module docstring above for the
    trade-off discussion.
    """

    def __init_subclass__(cls, **kw: Any) -> None:
        super().__init_subclass__(**kw)
        # `_register_input_handler` is a no-op when input_handler_name is empty
        # or _input_handler is None, so this is safe for any subclass — only
        # subclasses that declare a handler actually register. The
        # HasInputValue check both narrows the type for pyright and protects
        # against accidental use outside the input hierarchy.
        if issubclass(cls, HasInputValue):  # type: ignore[arg-type]
            cls._register_input_handler()  # type: ignore[attr-defined]


class UiInputActionButton(UiInput, Updatable, _InputHandlerAutoRegister):
    """Server-readable button.

    ``input.<id>()`` is an integer counter that starts at 0 and increments on
    each click. The class accessor :meth:`clicked` returns the current value as
    a reactive read; pair with :func:`shiny.reactive.event` to run code on each
    click without firing on the initial value.

    Demo of ``__init_subclass__`` registration — declaring the class
    auto-fires ``_register_input_handler()`` via the
    ``_InputHandlerAutoRegister`` parent. The handler below is registered
    under ``"shinyui.action"`` (NOT ``"shiny.action"``) to avoid colliding
    with shiny's own action-button handler; shiny's wire markup still
    routes through that one.
    """

    # Auto-registered via _InputHandlerAutoRegister.__init_subclass__ below.
    input_handler_name = "shinyui.action"

    @staticmethod
    def _input_handler(value: Any, name: Any, session: Any) -> int:
        """Coerce wire value to a plain int.

        (shiny's built-in handler returns an ActionButtonValue; we keep it
        simpler here as the demo doesn't actually receive wire traffic.)
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
