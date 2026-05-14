"""accordion_panel — layout child of accordion."""

from __future__ import annotations

from typing import overload

from htmltools import TagChild
from shiny.types import MISSING, MISSING_TYPE
from shiny.ui._accordion import AccordionPanel

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

    # Express overload: `with accordion_panel("Settings"): input_slider(...)`.
    @overload
    def __init__(
        self,
        title: str,
        *,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None: ...

    # Core overload: `accordion_panel("Settings", input_slider(...), ...)`.
    @overload
    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None: ...

    def __init__(
        self,
        title: str,
        *args: TagChild,
        value: str | MISSING_TYPE = MISSING,
        icon: TagChild | None = None,
    ) -> None:
        """Build an accordion panel.

        Parameters
        ----------
        title
            Panel header text. Also used as the panel's ``value`` identifier
            when ``value`` is not supplied.
        *args
            Child elements (any ``TagChild``). Omit when using the Express
            ``with accordion_panel(...):`` context-manager pattern.
        value
            String identifier for this panel within the accordion. Defaults to
            ``title``. The parent :class:`accordion` uses this when reporting
            which panels are open via ``input.<id>()`` / :meth:`accordion.open_panels`.
        icon
            Optional icon displayed in the panel header. Forwarded to
            :func:`shiny.ui.accordion_panel`.
        """
        self.title = title
        self._value: str | MISSING_TYPE = value
        self.icon = icon
        super().__init__(*args)

    @property
    def value(self) -> str:
        if isinstance(self._value, MISSING_TYPE):
            return self.title
        return self._value

    def tagify(self) -> AccordionPanel:  # type: ignore[override]
        import shiny.ui as _sui

        return _sui.accordion_panel(
            self.title,
            *self.children,
            value=self._value,
            icon=self.icon,
        )
