"""card — layout with optional full-screen toggle exposed as input value.

Wire id: ``shiny.ui.card`` accepts an ``id`` kwarg and shiny's card binding
pushes the full-screen state to ``input.<id>_full_screen``. The class accessor
:meth:`card.value_full_screen` reads that derived id directly (suffix
``_full_screen``) — there is no primary ``input.<id>()`` value.

Stage A scope note: server → client wiring for ``card.update(full_screen=)``
is out of scope (would require a small client-side JS adapter, since shiny
does not currently listen for a server-pushed ``full_screen`` message on
card). ``value_full_screen()`` reads the bound input correctly under unit
tests with a mocked session; in a live browser the value reflects whatever
state the user toggled client-side. The Stage B port to py-shiny may add the
JS hook.
"""

from __future__ import annotations

from typing import Any, Optional, overload

from htmltools import TagChild, Tagified

from ._children import AllowsChildren
from ._input_value import HasInputValue
from ._reactive import reactive_calc_method
from ._roles import UiLayout
from ._updatable import Updatable

_MISSING = object()


class card(UiLayout, AllowsChildren, HasInputValue, Updatable):
    """Card container with optional full-screen toggle.

    Wire id: ``input.<id>_full_screen`` is a boolean pushed by shiny's card
    binding when the user toggles full-screen mode. The class accessor
    :meth:`value_full_screen` returns the same.

    **Prototype note:** the browser-side JS that pushes ``full_screen`` is out
    of scope for the Stage A prototype. :meth:`value_full_screen` and
    :meth:`update` work correctly under mocked sessions and in unit tests, but
    in a live app the value stays ``False`` until the client-side JS lands in
    Stage B.

    Example
    -------
    .. code-block:: python

        c = card(output_code("summary"), id="main", full_screen=True)

        # In server:
        @reactive.calc
        def is_full():
            return c.value_full_screen()

        # Push a state change from the server:
        c.update(full_screen=False)
    """

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
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
    ) -> None:
        """Build a card as an Express context manager.

        Children come from the ``with`` block, not from positional args.

        Example
        -------
        .. code-block:: python

            with card(id="main", full_screen=True):
                output_code("summary")
                output_plot("plot", click=True)

        Parameters
        ----------
        id
            Input id used to read ``input.<id>_full_screen`` via
            :meth:`value_full_screen`.
        full_screen
            Initial full-screen state rendered into the HTML.
        height, max_height, min_height, fill, class_
            Forwarded verbatim to :func:`shiny.ui.card`; see shiny's docs for
            semantics.
        """
        ...

    # Core overload — inline positional children, the classic Shiny Core pattern.
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
    ) -> None:
        """Build a card with inline positional children.

        Example
        -------
        .. code-block:: python

            card(
                output_code("summary"),
                output_plot("plot", click=True),
                id="main",
                full_screen=True,
            )

        Parameters
        ----------
        *args
            Child elements (any ``TagChild``).
        id
            Input id used to read ``input.<id>_full_screen`` via
            :meth:`value_full_screen`.
        full_screen
            Initial full-screen state rendered into the HTML.
        height, max_height, min_height, fill, class_
            Forwarded verbatim to :func:`shiny.ui.card`; see shiny's docs for
            semantics.
        """
        ...

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
    def value_full_screen(self) -> bool:
        """Return whether the card is currently in full-screen mode.

        Shiny's card binding pushes the full-screen state to
        ``input.<id>_full_screen`` (not ``input.<id>()`` — the id itself has
        no primary value).
        """
        return bool(self._read_input("_full_screen"))

    def tagify(self) -> Tagified:
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
