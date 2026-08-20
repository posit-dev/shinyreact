"""``shinyreact.App``: ``shiny.App`` + full-document UI support.

Workaround for `posit-dev/py-shiny#2462
<https://github.com/posit-dev/py-shiny/issues/2462>`_: ``shiny.App`` cannot
accept a pre-rendered full HTML document (``htmltools.HTMLTextDocument``) with
extra dependencies — its ``_render_page()`` wraps every UI in its own
``HTMLDocument``, nesting ``<html>`` inside ``<html>``. Shiny's own
``App(ui=Path)`` route shows the intended mechanics (render the document with
``lib_prefix``, then register the dependency routes); this subclass does the
same for the document :func:`shinyreact.page_react_html` returns. Delete this
module when the upstream issue is fixed.

Shiny internals used (confined here, mirroring the ``shiny___`` wrapper policy
in ``pkg-r/R/bookmark.R``):

- ``App._ensure_web_dependencies()`` — the only way to register dependency
  file routes for a pre-rendered page.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from htmltools import HTMLTextDocument, TagList
from shiny import App as _ShinyApp

if TYPE_CHECKING:
    from htmltools import HTMLDependency


class ReactHtmlDocument(HTMLTextDocument):
    """The full-document UI returned by :func:`shinyreact.page_react_html`.

    An :class:`htmltools.HTMLTextDocument` that also remembers the directory
    the document was read from, so :class:`shinyreact.App` can serve the
    sibling assets (``ui.js`` etc.) the document references.
    """

    def __init__(
        self,
        html: str,
        *,
        src_dir: Path,
        deps: list[HTMLDependency],
        deps_replace_pattern: str,
    ) -> None:
        super().__init__(html, deps=deps, deps_replace_pattern=deps_replace_pattern)
        self.src_dir = src_dir


class App(_ShinyApp):
    """:class:`shiny.App` that also accepts :func:`page_react_html`'s document.

    A drop-in replacement — ``from shinyreact import App`` — needed only when
    the UI is the full HTML document returned by :func:`page_react_html`
    (see posit-dev/py-shiny#2462). Every other UI type behaves exactly like
    ``shiny.App``.

    When the UI is a :class:`ReactHtmlDocument`, the document's directory is
    mounted at ``/`` automatically (unless ``static_assets`` is given), so the
    scripts and stylesheets the document references are served — the manual
    ``static_assets={"/": ...}`` mount ``shiny.App`` would need is implied.
    """

    def __init__(
        self,
        ui: Any,
        server: Any,
        **kwargs: Any,
    ) -> None:
        if not isinstance(ui, HTMLTextDocument):
            super().__init__(ui, server, **kwargs)
            return

        if kwargs.get("bookmark_store", "disable") != "disable":
            raise NotImplementedError(
                "A full-document UI (page_react_html) does not support "
                "bookmark_store yet: the document is rendered once at startup, "
                "but bookmark restore needs a per-request render. Use "
                "page_react() inside a `def app_ui(request)` function instead."
            )
        if kwargs.get("static_assets") is None and isinstance(ui, ReactHtmlDocument):
            kwargs["static_assets"] = {"/": ui.src_dir}

        # Construct with an empty page (this registers shiny's own web assets),
        # then replace the rendered UI with the document — the same steps
        # shiny's App(ui=Path) route performs internally.
        super().__init__(TagList(), server, **kwargs)
        rendered = ui.render(lib_prefix=self.lib_prefix)
        self._ensure_web_dependencies(rendered["dependencies"])
        self.ui = rendered
