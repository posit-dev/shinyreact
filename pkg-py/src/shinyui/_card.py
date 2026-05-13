"""card — layout with optional full-screen toggle exposed as input value.

NOTE: real wire-level `full_screen` input is out of scope for the Stage A
prototype (would require client-side JS). The `full_screen_value()` accessor
exists for the class-design test path; in a live app it will be None until
client JS is added.

`shiny.ui.card` already accepts an `id` kwarg and reports
``input.<id>_full_screen`` as a bool when the browser's card JS fires, but
that browser JS is not wired in the prototype. This class uses the plain
``self.id`` key so unit tests can mock it straightforwardly.
"""

from __future__ import annotations

from typing import Any, Optional, overload

from htmltools import Tag, TagChild

from ._children import AllowsChildren
from ._input_value import HasInputValue
from ._reactive import reactive_calc_method
from ._roles import UiLayout
from ._updatable import Updatable

_MISSING = object()


class card(UiLayout, AllowsChildren, HasInputValue, Updatable):  # noqa: N801
    """Card container; full-screen state is available via full_screen_value().

    No custom input handler is registered — shiny's own card binding handles
    the wire format when client JS is present. full_screen_value() reads the
    input keyed by self.id (mocked in tests).
    """

    # Express overload: `with card(id="m"): child_a; child_b` — no positional
    # children. Listed first so IDEs prefer it for the `with ...:` idiom.
    @overload
    def __init__(
        self,
        *,
        id: str,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None: ...

    # Core overload: `card(child_a, child_b, id="m", ...)` — inline positional
    # children, the classic Shiny Core pattern.
    @overload
    def __init__(
        self,
        *args: TagChild,
        id: str,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None: ...

    def __init__(
        self,
        *args: TagChild,
        id: str,
        full_screen: bool = False,
        height: Optional[str] = None,
        max_height: Optional[str] = None,
        min_height: Optional[str] = None,
        fill: bool = True,
        class_: Optional[str] = None,
    ) -> None:
        self._full_screen = full_screen
        self.height = height
        self.max_height = max_height
        self.min_height = min_height
        self.fill = fill
        self.class_ = class_
        super().__init__(*args, id=id)

    @reactive_calc_method
    def full_screen_value(self) -> bool:
        """Return whether the card is currently in full-screen mode.

        Shiny's card binding pushes the full-screen state to
        ``input.<id>_full_screen`` (not ``input.<id>()`` — the id itself has
        no primary value).
        """
        return bool(self._read_input("_full_screen"))

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        kwargs: dict[str, Any] = {
            "full_screen": self._full_screen,
            "fill": self.fill,
            "id": self.id,
        }
        if self.height is not None:
            kwargs["height"] = self.height
        if self.max_height is not None:
            kwargs["max_height"] = self.max_height
        if self.min_height is not None:
            kwargs["min_height"] = self.min_height
        if self.class_ is not None:
            kwargs["class_"] = self.class_

        # `shiny.ui.card` accepts arbitrary TagChild members — including our
        # Tagifiable accordion / input_slider / etc. — so we hand them in
        # unchanged. A single .tagify() on the result lets htmltools' walker
        # resolve our Tagifiable descendants chain-style. (Card has no
        # isinstance check on children, unlike accordion's AccordionPanel.)
        return _sui.card(*self.children, **kwargs).tagify()

    def update(
        self,
        *,
        full_screen: bool = _MISSING,  # type: ignore[assignment]
    ) -> None:
        """Send a full-screen state update to the client.

        Parameters
        ----------
        full_screen
            Target full-screen state to apply on the client.
        """
        sess = self._require_session(for_op="update")
        if full_screen is _MISSING:
            return
        # There is no shiny.ui.update_card today; use send_input_message directly.
        sess.send_input_message(self.id, {"full_screen": full_screen})
