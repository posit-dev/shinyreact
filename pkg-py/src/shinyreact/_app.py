"""``shinyreact.ReactApp``: ``shiny.App`` + auto-mounted document assets.

``shiny.App`` accepts the full-document UI itself via ``ui.PageDocument``
(py-shiny#2475, currently consumed as a git dependency — see issue #216 for
the release-pin swap). The only thing it does not do is serve the sibling
files the document references (``ui.js`` etc.); ``ReactApp`` fills that gap by
mounting the document's directory at ``/`` when no ``static_assets`` is given.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from shiny import App as _ShinyApp
from shiny import ui as _shiny_ui

if TYPE_CHECKING:
    from htmltools import HTMLDependency


class ReactHtmlDocument(_shiny_ui.PageDocument):
    """The full-document UI returned by :func:`shinyreact.page_react_html`.

    A :class:`shiny.ui.PageDocument` that also remembers the directory the
    document was read from, so :class:`ReactApp` can serve the sibling assets
    (``ui.js`` etc.) the document references.
    """

    def __init__(
        self,
        html: str,
        *,
        src_dir: Path,
        extra_deps: list[HTMLDependency],
        deps_replace_pattern: str,
    ) -> None:
        super().__init__(
            html, extra_deps=extra_deps, deps_replace_pattern=deps_replace_pattern
        )
        self.src_dir = src_dir


class ReactApp(_ShinyApp):
    """:class:`shiny.App` that serves :func:`page_react_html`'s sibling assets.

    A drop-in replacement — ``from shinyreact import ReactApp`` — that mounts
    the document's directory at ``/`` (unless ``static_assets`` is given), so
    the scripts and stylesheets the document references are served without a
    manual ``static_assets={"/": ...}`` mount. Every other UI type behaves
    exactly like ``shiny.App``.

    For bookmarked apps, pass a UI *function* (``lambda request:
    page_react_html()``) so the restore payload renders per request; note the
    auto-mount only applies to a direct :class:`ReactHtmlDocument` argument,
    so pair a UI function with an explicit ``static_assets``.
    """

    def __init__(self, ui: Any, server: Any, **kwargs: Any) -> None:
        if isinstance(ui, ReactHtmlDocument) and kwargs.get("static_assets") is None:
            kwargs["static_assets"] = {"/": ui.src_dir}
        super().__init__(ui, server, **kwargs)
