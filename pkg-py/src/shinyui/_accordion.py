"""accordion — layout with collapsible panels; open-panel set exposed as input value.

Implementation note: shiny's accordion already registers its own input binding that
pushes the open-panel list to the server as a list.  No custom input handler is
registered here (approach A); open_panels() coerces list -> tuple at read time.
"""

from __future__ import annotations

from typing import Any, Optional, overload

from htmltools import Tag

from ._accordion_panel import accordion_panel
from ._children import AllowsChildren
from ._input_value import HasInputValue
from ._reactive import reactive_calc_method
from ._roles import UiLayout
from ._updatable import Updatable

_MISSING = object()


class accordion(UiLayout, AllowsChildren, HasInputValue, Updatable):  # noqa: N801
    """Accordion container with collapsible panels.

    Wire id: ``input.<id>()`` is a list of the currently-open panel values,
    pushed by shiny's accordion binding. The class accessor :meth:`open_panels`
    returns the same set as a ``tuple[str, ...]``.

    Example
    -------
    .. code-block:: python

        acc = accordion(
            accordion_panel("Settings", input_slider("n", "N", 1, 10, 5)),
            accordion_panel("Diagnostics", output_code("diag")),
            id="acc",
            open="Settings",
        )

        # In server:
        acc.open_panels()               # tuple of open panel values

        # Push open/closed state from the server:
        acc.update(open=("Settings", "Diagnostics"))
        acc.update(open=False)          # close all
    """

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
    @overload
    def __init__(
        self,
        *,
        id: str,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None:
        """Build an accordion as an Express context manager.

        Children come from the ``with`` block, not from positional args.

        Example
        -------
        .. code-block:: python

            with accordion(id="acc", open="Settings"):
                accordion_panel("Settings", input_slider("n", "N", 1, 10, 5))
                accordion_panel("Diagnostics", output_code("diag"))

        Parameters
        ----------
        id
            Input id; the open-panel list is available as ``input.<id>()``
            server-side, or via :meth:`open_panels`.
        open
            Initially open panel(s). Pass a string for a single panel, a
            tuple for multiple, ``True`` to open all, or ``False`` to close
            all. ``None`` delegates to shiny's default (first panel open).
        multiple
            Allow more than one panel to be open at a time.
        class_, width, height
            Forwarded verbatim to :func:`shiny.ui.accordion`; see shiny's
            docs for semantics.
        """
        ...

    # Core overload — inline positional :class:`accordion_panel` instances.
    @overload
    def __init__(
        self,
        *args: accordion_panel,
        id: str,
        open: Optional[str | tuple[str, ...] | bool] = None,
        multiple: bool = True,
        class_: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
    ) -> None:
        """Build an accordion with inline positional panels.

        Example
        -------
        .. code-block:: python

            accordion(
                accordion_panel("Settings", input_slider("n", "N", 1, 10, 5)),
                accordion_panel("Diagnostics", output_code("diag")),
                id="acc",
                open="Settings",
            )

        Parameters
        ----------
        *args
            Child :class:`accordion_panel` instances.
        id
            Input id; the open-panel list is available as ``input.<id>()``
            server-side, or via :meth:`open_panels`.
        open
            Initially open panel(s). Pass a string for a single panel, a
            tuple for multiple, ``True`` to open all, or ``False`` to close
            all. ``None`` delegates to shiny's default (first panel open).
        multiple
            Allow more than one panel to be open at a time.
        class_, width, height
            Forwarded verbatim to :func:`shiny.ui.accordion`; see shiny's
            docs for semantics.
        """
        ...

    def __init__(
        self,
        *args: accordion_panel,
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

        # `shiny.ui.accordion` does an explicit isinstance(panel, AccordionPanel)
        # check on its positional args and rejects rendered Tags. So instead of
        # calling child.tagify() (which now returns Tag), we read each child's
        # stored state and build shiny's AccordionPanel wrapper inline. A single
        # .tagify() on the outer result lets htmltools' walker resolve any
        # remaining Tagifiable descendants (e.g. an input_slider inside a panel).
        panels = [
            _sui.accordion_panel(
                child.title,  # type: ignore[union-attr]
                *child.children,  # type: ignore[union-attr]
                value=child._value,  # type: ignore[union-attr]
                icon=child.icon,  # type: ignore[union-attr]
            )
            for child in self.children
        ]
        return _sui.accordion(
            *panels,
            id=self.id,
            open=self._open,
            multiple=self.multiple,
            class_=self.class_,
            width=self.width,
            height=self.height,
        ).tagify()

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
