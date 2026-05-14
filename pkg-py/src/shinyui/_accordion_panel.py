"""accordion_panel — layout child of accordion."""

from __future__ import annotations

from typing import overload

from htmltools import Tag, TagChild
from shiny.types import MISSING, MISSING_TYPE

from ._children import AllowsChildren
from ._roles import UiLayout


class accordion_panel(UiLayout, AllowsChildren):  # noqa: N801
    """A single collapsible panel within an :class:`accordion`.

    ``accordion_panel`` has no wire id of its own. The parent
    :class:`accordion` identifies each panel by its ``value`` attribute (which
    defaults to ``title`` when not supplied explicitly). Pass that string to
    :meth:`accordion.update` to open or close a specific panel.

    Example
    -------
    .. code-block:: python

        accordion_panel("Settings", input_slider("seed", "Seed", 1, 100, 42))

        # Express pattern:
        with accordion_panel("Settings"):
            input_slider("seed", "Seed", 1, 100, 42)
    """

    # Express overload — listed first so IDEs prefer it for `with ...:` idioms.
    @overload
    def __init__(
        self,
        title: str,
        *,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None:
        """Build an accordion panel as an Express context manager.

        Children come from the ``with`` block, not from positional args.

        Example
        -------
        .. code-block:: python

            with accordion_panel("Settings"):
                input_slider("seed", "Seed", 1, 100, 42)

        Parameters
        ----------
        title
            Panel header text. Also used as the panel's ``value`` identifier
            when ``value`` is not supplied.
        value
            String identifier for this panel within the accordion. Defaults
            to ``title``. The parent :class:`accordion` uses this when
            reporting which panels are open.
        icon
            Optional icon displayed in the panel header. Forwarded to
            :func:`shiny.ui.accordion_panel`.
        """
        ...

    # Core overload — inline positional children.
    @overload
    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None:
        """Build an accordion panel with inline positional children.

        Example
        -------
        .. code-block:: python

            accordion_panel(
                "Settings",
                input_slider("seed", "Seed", 1, 100, 42),
            )

        Parameters
        ----------
        title
            Panel header text. Also used as the panel's ``value`` identifier
            when ``value`` is not supplied.
        *args
            Child elements (any ``TagChild``).
        value
            String identifier for this panel within the accordion. Defaults
            to ``title``. The parent :class:`accordion` uses this when
            reporting which panels are open.
        icon
            Optional icon displayed in the panel header. Forwarded to
            :func:`shiny.ui.accordion_panel`.
        """
        ...

    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None:
        self.title = title
        self._value: str | MISSING_TYPE = value
        self.icon = icon
        super().__init__(*args)

    @property
    def value(self) -> str:
        if isinstance(self._value, MISSING_TYPE):
            return self.title
        return self._value

    def tagify(self) -> Tag:
        # Honor the UiComponent.tagify() -> Tag contract by chaining .tagify()
        # on shiny's AccordionPanel wrapper. shiny's AccordionPanel.tagify()
        # requires `_accordion_id` (normally stamped by the parent accordion's
        # `_sui.accordion(*panels)` call). For standalone rendering we set a
        # placeholder keyed off the panel's value. The parent :class:`accordion`
        # builds its own AccordionPanel wrappers from this instance's
        # attributes (it can't reuse the rendered Tag — shiny.ui.accordion
        # does an isinstance(panel, AccordionPanel) check on its positional
        # args).
        import shiny.ui as _sui

        panel = _sui.accordion_panel(
            self.title,
            *self.children,
            value=self._value,
            icon=self.icon,
        )
        panel._accordion_id = f"_orphan_{self.value}"
        return panel.tagify()
