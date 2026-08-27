"""``shinyreact.ReactApp``: a ``shiny.App`` whose UI is discovered, not passed.

``shiny.App`` accepts the full-document UI itself via ``ui.PageDocument``
(py-shiny#2475, currently consumed as a git dependency — see issue #216 for
the release-pin swap). ``ReactApp`` adds the two things it does not do:
discover the ui.tsx-pattern UI next to the app file, and serve the sibling
assets a full document references.
"""

from __future__ import annotations

import sys
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
    """:class:`shiny.App` for the ui.tsx pattern — the UI is discovered.

    The app file is just the server::

        from shinyreact import ReactApp

        app = ReactApp(server, bookmark_store="url")

    With no ``ui=``, the UI is discovered next to the calling module the same
    way :func:`set_react_page` discovers it: ``www/index.html`` present →
    :func:`page_react_html` (and the document's directory is mounted at ``/``
    so the assets it references are served); otherwise → :func:`page_react`
    (``www/ui.js`` / ``www/ui.css``, served by the dependency itself). The
    discovered UI is a function of the request, so it re-renders per request
    and bookmark restore works with no further wiring.

    ``ui=`` overrides discovery and behaves exactly like ``shiny.App``'s
    ``ui`` argument — except that a direct :class:`ReactHtmlDocument` (what
    :func:`page_react_html` returns) still gets its directory auto-mounted
    unless ``static_assets`` is given. Note the discovery reads the
    *immediate* calling frame (like :func:`page_react_dep`), so a helper that
    wraps ``ReactApp(...)`` must pass ``ui=`` explicitly.
    """

    def __init__(self, server: Any, *, ui: Any = None, **kwargs: Any) -> None:
        if ui is None:
            # Import here: _page imports ReactHtmlDocument from this module.
            from ._page import page_react, page_react_html

            caller_file = sys._getframe(1).f_globals.get("__file__")
            # No __file__ (REPL / exec'd code): fall back to CWD, matching
            # page_react() / page_react_html().
            app_dir = Path(caller_file).parent if caller_file else Path.cwd()
            src_dir = app_dir / "www"
            index_path = src_dir / "index.html"

            # Mount the document dir whenever it *could* be needed. The mode is
            # decided per request below, but `static_assets` is a constructor
            # argument, so it cannot be: mounting a directory the app never
            # serves from is harmless, while failing to mount one it does serve
            # from is a 404 per asset.
            if src_dir.is_dir() and "static_assets" not in kwargs:
                kwargs["static_assets"] = {"/": src_dir}

            def discovered_ui(request: Any) -> Any:
                # Re-checked per request, not latched at construction: the UI is
                # already a per-request function, so creating or deleting
                # www/index.html during a dev session now switches modes without
                # a restart. `exists()` is one stat call per page render.
                if index_path.exists():
                    return page_react_html(index_path)
                return page_react(src_dir=src_dir)

            ui = discovered_ui

        if isinstance(ui, ReactHtmlDocument) and "static_assets" not in kwargs:
            kwargs["static_assets"] = {"/": ui.src_dir}
        super().__init__(ui, server, **kwargs)
