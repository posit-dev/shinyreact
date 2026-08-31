"""``shinyreact.ReactApp``: a ``shiny.App`` whose UI is discovered, not passed.

``shiny.App`` accepts the full-document UI itself via ``ui.PageDocument``
(py-shiny#2475). ``ReactApp`` adds the two things it does not do: discover the
ui.tsx-pattern UI next to the app file, and serve the sibling assets a full
document references.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from shiny import App as _ShinyApp
from shiny import ui as _shiny_ui
from shiny.types import MISSING, MISSING_TYPE

from ._dep import ShinyreactJs, _serves_bundle

if TYPE_CHECKING:
    from htmltools import HTMLDependency

    StaticAssets = str | Path | Mapping[str, str | Path]


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
    ) -> None:
        super().__init__(html, extra_deps=extra_deps)
        self.src_dir = src_dir


def _add_react_dir(
    static_assets: StaticAssets | None | MISSING_TYPE, react_dir: Path | None
) -> StaticAssets | None:
    """Resolve ``static_assets`` into what :class:`shiny.App` should mount.

    ``react_dir`` is the directory a full HTML document's relative asset URLs
    resolve against, so it has to be served at ``"/"``. It is *added to* what
    the author asked for rather than replacing it, so an unrelated mount cannot
    silently stop ``ui.js`` from being served. Four cases:

    - not passed (``MISSING``) → ``react_dir`` at ``"/"``
    - ``None`` → nothing; the author said no static assets and meant it
    - a mapping → their mounts, plus ``react_dir`` at ``"/"`` if they left
      ``"/"`` free
    - a bare path → theirs only; a bare path *is* the ``"/"`` mount, so they
      have already said which directory serves the document's siblings
    """
    author_mounts: Mapping[str, str | Path]
    if isinstance(static_assets, MISSING_TYPE):
        author_mounts = {}
    elif static_assets is None or not isinstance(static_assets, Mapping):
        return static_assets
    else:
        author_mounts = static_assets

    if react_dir is None or not react_dir.is_dir():
        return author_mounts or None
    # Author's keys last, so an explicit "/" replaces ours. Shiny sorts mount
    # points by descending length itself, so insertion order is irrelevant.
    return {"/": react_dir, **author_mounts}


class ReactApp(_ShinyApp):
    """:class:`shiny.App` for the ui.tsx pattern — the UI is discovered.

    The app file is just the server::

        from shinyreact import ReactApp

        app = ReactApp(server, bookmark_store="url")

    With no ``ui=``, the UI is discovered next to the calling module the same
    way :func:`set_react_page` discovers it: ``www/index.html`` present →
    :func:`page_react_html`; otherwise → :func:`page_react` (``www/ui.js`` /
    ``www/ui.css``, served by the dependency itself). The discovered UI is a
    function of the request, so it re-renders per request — which is what makes
    ``bookmark_store=`` work with no further wiring, and what lets the mode
    switch mid-session when you create or delete ``www/index.html``.

    ``ui=`` overrides discovery and behaves exactly like ``shiny.App``'s ``ui``
    argument, except that a direct :class:`ReactHtmlDocument` (what
    :func:`page_react_html` returns) still gets its directory mounted. Note the
    discovery reads the *immediate* calling frame (like :func:`page_react_dep`),
    so a helper that wraps ``ReactApp(...)`` must pass ``ui=`` explicitly.

    Args:
        server: The server function, as for :class:`shiny.App`.
        ui: Overrides UI discovery. Anything ``shiny.App`` accepts.
        static_assets: Extra static mounts. **Added to** the React asset
            directory rather than replacing it — see below. Defaults to
            :data:`shiny.types.MISSING`, not ``None``, so that passing ``None``
            explicitly can mean "no static assets at all".
        bookmark_store: ``"url"`` / ``"server"`` to enable bookmarking, as for
            :class:`shiny.App`. Requires a callable UI, which discovery
            provides; a static ``ui=page_react_html(...)`` raises.
        shinyreact_js: Who supplies ``shinyreact.js`` / ``shinyreact.css`` to
            the discovered UI: ``"server"`` (default) or ``"client"`` for an
            npm-tier app whose bundle imports ``@posit/shinyreact``. Ignored
            when ``ui=`` is passed — build that UI with
            ``shinyreact_js="client"`` yourself.
        **kwargs: Forwarded to :class:`shiny.App` (``debug=``, ``test_mode=``).

    Static assets
    -------------
    A full HTML document references its bundle with a plain relative URL
    (``<script src="ui.js">``), so *something* has to serve the directory the
    document lives in. ``ReactApp`` mounts it at ``/`` for you:

    - **discovery mode** — ``www/`` next to the app file, mounted whenever the
      directory exists. It is mounted even in ``page_react()`` mode, where the
      dependency serves the assets itself and the mount is unused: the mode is
      decided per *request* while ``static_assets`` is a *constructor*
      argument, so an unused mount is the only way to keep both modes working.
      An unused mount is harmless; a missing one is a 404 per asset.
    - **``ui=page_react_html(...)``** — the document's own directory, from
      :attr:`ReactHtmlDocument.src_dir`.

    Your ``static_assets`` is **merged with** that mount, not substituted for
    it, so adding an unrelated mount doesn't take the bundle down with it::

        ReactApp(server, static_assets={"/data": DATA_DIR})
        # serves /data from DATA_DIR *and* / from www/

    You win wherever you actually collide with it, and there are three ways to::

        ReactApp(server, static_assets={"/": DIST_DIR})  # explicit "/" key
        ReactApp(server, static_assets=DIST_DIR)         # a bare path *is* "/"
        ReactApp(server, static_assets=None)             # nothing mounted

    The last one is why the default is :data:`shiny.types.MISSING` rather than
    ``None``: with ``None`` as the default there would be no way to say "mount
    nothing", since not passing the argument and passing ``None`` would look
    identical from in here.

    Shiny requires every mount path to be absolute, and sorts mount points by
    descending length, so a nested mount is matched before ``/``.
    """

    def __init__(
        self,
        server: Any,
        *,
        ui: Any = None,
        static_assets: StaticAssets | None | MISSING_TYPE = MISSING,
        bookmark_store: Literal["url", "server", "disable"] = "disable",
        shinyreact_js: ShinyreactJs = "server",
        **kwargs: Any,
    ) -> None:
        # Validate now rather than at first page render: a typo should fail at
        # startup, next to the call that made it.
        _serves_bundle(shinyreact_js)

        # The directory holding the React bundle, to be mounted at "/".
        react_dir: Path | None = None

        if ui is None:
            # Import here: _page imports ReactHtmlDocument from this module.
            from ._page import page_react, page_react_html

            caller_file = sys._getframe(1).f_globals.get("__file__")
            # No __file__ (REPL / exec'd code): fall back to CWD, matching
            # page_react() / page_react_html().
            app_dir = Path(caller_file).parent if caller_file else Path.cwd()
            src_dir = app_dir / "www"
            index_path = src_dir / "index.html"
            react_dir = src_dir

            def discovered_ui(request: Any) -> Any:
                # Re-checked per request, not latched at construction: the UI is
                # already a per-request function, so creating or deleting
                # www/index.html during a dev session now switches modes without
                # a restart. `exists()` is one stat call per page render.
                if index_path.exists():
                    return page_react_html(index_path, shinyreact_js=shinyreact_js)
                return page_react(src_dir=src_dir, shinyreact_js=shinyreact_js)

            ui = discovered_ui

        elif isinstance(ui, ReactHtmlDocument):
            react_dir = ui.src_dir

            if bookmark_store != "disable":
                # Shiny would raise here too ("App(ui=) must be a function"),
                # but the fix a shinyreact author needs is specific, and the
                # obvious workaround is wrong: wrapping *this object* in a
                # `lambda request: doc` yields a callable UI that never
                # restores, because page_react_html() reads the RestoreContext
                # when it builds the config tag — i.e. already, before any
                # request. The call has to happen per request.
                raise TypeError(
                    "bookmark_store= needs a UI that is rebuilt per request, but"
                    " ui=page_react_html(...) is a single document built once."
                    " Drop ui= and let ReactApp discover www/index.html, or pass"
                    " the call itself:"
                    ' ui=lambda request: page_react_html("client/index.html").'
                )

        super().__init__(
            ui,
            server,
            static_assets=_add_react_dir(static_assets, react_dir),
            bookmark_store=bookmark_store,
            **kwargs,
        )
