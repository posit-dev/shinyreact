"""UiAccordion — layout with collapsible panels; open-panel set exposed as input value.

Implementation note: shiny's accordion already registers its own input binding that
pushes the open-panel list to the server as a list.  No custom input handler is
registered here (approach A); open_panels() coerces list -> tuple at read time.
"""

from __future__ import annotations

from typing import Any, Optional

from htmltools import Tag

from ._accordion_panel import UiAccordionPanel
from ._children import AllowsChildren
from ._input_value import HasInputValue
from ._reactive import reactive_calc_method
from ._roles import UiLayout
from ._updatable import Updatable

_MISSING = object()


class UiAccordion(UiLayout, AllowsChildren, HasInputValue, Updatable):
    """Accordion container; open-panel set is available via open_panels().

    No custom input handler is registered — shiny's own accordion binding handles
    the wire format.  open_panels() coerces the received list to a tuple at read time.
    """

    def __init__(
        self,
        *args: UiAccordionPanel,
        id: str,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None:
        self._open = open
        self.multiple = multiple
        self.class_ = class_
        self.width = width
        self.height = height
        super().__init__(*args, id=id)

    @reactive_calc_method
    def open_panels(self) -> tuple[str, ...]:
        """Return the currently open accordion panel values as a tuple."""
        return tuple(self._read_input() or ())

    def tagify(self) -> Tag:
        import shiny.ui as _sui

        # Each child's tagify() returns an AccordionPanel that shiny.ui.accordion
        # accepts directly. Deep-resolve the result so any Tagifiable descendants
        # within the panels' content (e.g. an input_slider inside a panel) are
        # fully expanded before htmltools renders.
        panels: list = [child.tagify() for child in self.children]  # type: ignore[union-attr]
        return self._deep_tagify(
            _sui.accordion(
                *panels,
                id=self.id,
                open=self._open,
                multiple=self.multiple,
                class_=self.class_,
                width=self.width,
                height=self.height,
            )
        )

    def update(
        self,
        *,
        open: tuple[str, ...] | list[str] | bool = _MISSING,  # type: ignore[assignment]
        show: tuple[str, ...] | list[str] | str = _MISSING,  # type: ignore[assignment]
        hide: tuple[str, ...] | list[str] | str = _MISSING,  # type: ignore[assignment]
    ) -> None:
        """Update the accordion's open/closed state.

        Parameters
        ----------
        open
            Panel value(s) to set as open (closes all others).  Passed to
            shiny.ui.update_accordion as ``show=``.  Pass ``True`` to open all,
            ``False`` to close all.
        show
            Panel value(s) to open without closing others, via
            shiny.ui.update_accordion_panel per target.
        hide
            Panel value(s) to close without affecting others, via
            shiny.ui.update_accordion_panel per target.
        """
        import shiny.ui as _sui

        sess = self._require_session(for_op="update")

        if open is not _MISSING:
            # update_accordion sends method="set" — sets which panels are open.
            show_val: Any = list(open) if isinstance(open, (tuple, list)) else open
            _sui.update_accordion(self.id, show=show_val, session=sess)

        if show is not _MISSING:
            targets = [show] if isinstance(show, str) else list(show)
            for target in targets:
                _sui.update_accordion_panel(self.id, target, show=True, session=sess)

        if hide is not _MISSING:
            targets = [hide] if isinstance(hide, str) else list(hide)
            for target in targets:
                _sui.update_accordion_panel(self.id, target, show=False, session=sess)


def accordion(*args: UiAccordionPanel, id: str, **kwargs: Any) -> UiAccordion:
    """Create a UiAccordion.

    Parameters
    ----------
    *args
        :class:`UiAccordionPanel` children.
    id
        Input id; available as ``input.id()`` in the server, or via
        ``accordion_obj.open_panels()``.
    **kwargs
        Forwarded to :class:`UiAccordion` (``open``, ``multiple``, ``class_``,
        ``width``, ``height``).
    """
    return UiAccordion(*args, id=id, **kwargs)
