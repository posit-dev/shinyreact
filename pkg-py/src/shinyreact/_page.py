from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, cast

from htmltools import HTML, HTMLDependency, Tag, TagChild, TagList
from shiny.express.ui import page_opts
from shiny.render.renderer import Renderer
from shiny.session import get_current_session

from ._app import ReactHtmlDocument
from ._bookmark import _config_script_tag
from ._dep import ShinyreactJs, _dep, _dep_page, _file_mtime_int, _serves_bundle

if TYPE_CHECKING:
    # Private, but it is the only name for HTMLDependency's stylesheet entry.
    from htmltools._core import ScriptItem, StylesheetItem


def page_bare(
    *args: TagChild,
    title: str | None = None,
    lang: str = "en",
    **kwargs: Any,
) -> Tag:
    """Create a bare HTML page with only Shiny dependencies.

    This is the escape hatch for fully custom setups that don't need the
    shinyreact JS/CSS. It wraps ``shiny.ui.page_bootstrap()`` with minimal
    defaults.

    Pass :class:`~htmltools.HTMLDependency` objects as positional arguments to
    include them in the page — Shiny automatically hoists them to ``<head>``.

    Args:
        *args: Child tags or HTMLDependency objects to include in the page.
        title: Page title.
        lang: HTML ``lang`` attribute.
        **kwargs: Forwarded to :func:`shiny.ui.page_bootstrap` — its own
            ``theme=``, or tag attributes for the page. Deliberately not
            surfaced as named parameters: in the ui.tsx pattern the client owns
            styling, so Bootstrap theming is a passthrough, not part of this
            API.
    """
    from shiny.ui import page_bootstrap

    return page_bootstrap(
        *args,
        title=title,
        lang=lang,
        **kwargs,
    )


def _resolve_react_dirs(
    src_dir: str | Path | None, caller_dir: Path
) -> tuple[Path, str]:
    """Resolve ``page_react``'s asset dir and derive the app name.

    Returns ``(base_dir, app_name)``. ``app_name`` is the app folder's name:
    when the asset dir is the conventional ``www/``, its parent (the app dir)
    names the app; otherwise the asset dir itself does.
    """
    if src_dir is None:
        base_dir = caller_dir / "www"
    else:
        src_dir = Path(src_dir)
        base_dir = src_dir if src_dir.is_absolute() else caller_dir / src_dir
    app_name = base_dir.parent.name if base_dir.name == "www" else base_dir.name
    return base_dir, app_name


def page_react(
    *args: TagChild,
    src_dir: str | Path | None = None,
    js_file: str = "ui.js",
    css_file: str | None = "ui.css",
    title: str | None = None,
    lang: str = "en",
    shinyreact_js: ShinyreactJs = "server",
    **kwargs: Any,
) -> Tag:
    """Create a React page from conventional assets — no HTML file required.

    The zero-configuration page for the ui.tsx pattern: the server emits no
    body HTML at all. It attaches the shinyreact bundle plus your app's entry
    assets, discovered at ``www/ui.js`` and ``www/ui.css`` (relative to the
    calling module). Your JS owns the DOM — create and append your own mount
    container::

        const root = ReactDOM.createRoot(
          document.body.appendChild(document.createElement("div")),
        );

    ``ui.js`` is required (a missing file warns, pointing at the resolved
    path); ``ui.css`` is attached only when it exists. Both are served as an
    :class:`~htmltools.HTMLDependency` versioned by ``ui.js``'s mtime, so the
    browser re-fetches after every edit — unlike raw ``<script src=...>``
    tags in a hand-written HTML file, which the browser caches.

    Args:
        *args: Extra children or :class:`~htmltools.HTMLDependency` objects.
        src_dir: Directory containing the assets. Defaults to ``www/`` next
            to the calling module; relative paths resolve against the caller.
        js_file: JS entry filename within ``src_dir`` (default ``"ui.js"``).
        css_file: CSS filename within ``src_dir`` (default ``"ui.css"``).
        title: Page title. Defaults to the app folder's name (``src_dir``'s
            parent when ``src_dir`` is a ``www/`` dir).
        lang: HTML ``lang`` attribute.
        shinyreact_js: Who supplies ``shinyreact.js`` (and
            ``shinyreact.css``) to the page.

            - ``"server"`` (default) — the shinyreact package serves them as an
              :class:`~htmltools.HTMLDependency`. What a no-build app needs,
              and what makes ``window.shinyreact`` exist.
            - ``"client"`` — your own bundle imports ``@posit/shinyreact`` and
              ships its own copy, so the server sends nothing. Serving them too
              would put two copies of React and the hooks on one page.

            The ``#shinyreact-config`` tag is emitted either way — it carries
            the protocol version and any bookmark restore payload.
        **kwargs: Forwarded to :func:`page_bare`, and on to
            :func:`shiny.ui.page_bootstrap`.
    """
    caller_file = sys._getframe(1).f_globals.get("__file__")
    caller_dir = Path(caller_file).parent if caller_file else Path.cwd()
    base_dir, app_name = _resolve_react_dirs(src_dir, caller_dir)
    return page_bare(
        _dep_page(shinyreact_js),
        page_react_dep(
            src_dir=base_dir,
            js_file=js_file,
            css_file=css_file,
            name=app_name,
        ),
        *args,
        title=title if title is not None else app_name,
        lang=lang,
        **kwargs,
    )


def page_react_dep(
    *,
    src_dir: str | Path | None = None,
    js_file: str = "ui.js",
    css_file: str | None = "ui.css",
    name: str | None = None,
) -> HTMLDependency:
    """Build an HTMLDependency for a React app's JS and CSS entry points.

    The JS file's mtime is the dependency version, so the
    ``/lib/<name>-<version>/`` URL changes on every rebuild and the browser
    re-fetches. That is what you want while developing, and the wrong thing for
    a published package — an mtime is whatever the install happened to write, so
    it is neither stable across machines nor meaningful to a reader. There is no
    ``version=`` here on purpose: a package shipping a fixed version should
    build its own :class:`~htmltools.HTMLDependency` (the same advice as for a
    classic, non-module bundle), which is five lines and leaves nothing about
    the dependency implicit.

    Both the script and the stylesheet are attached only when the file exists
    inside the resolved ``src_dir``, so a bundle that ships no CSS — or that has
    not been built yet — does not emit a tag pointing at a 404. Pass
    ``css_file=None`` to never attach a stylesheet. A missing ``js_file`` warns,
    since it is the entry point and an empty dependency would otherwise fail
    silently.

    Path resolution
    ---------------
    The base directory is ``src_dir`` when given. Passing it explicitly is
    recommended for library authors — the inference below reads the *immediate*
    calling frame, so wrapping this function in a helper resolves against the
    wrapper's directory rather than the app's.

    When ``src_dir`` is omitted it is inferred:

    1. **Module call (typical):** when the caller is a regular Python module
       (``__file__`` set), paths resolve against the module's directory. This
       is the expected usage::

           # /path/to/my-app/app.py
           from shinyreact import page_react_dep

           dep = page_react_dep(js_file="bundle.js")
           # dep.source["subdir"] == "/path/to/my-app"
           # dep.name == "my-app"
           # version == mtime of /path/to/my-app/bundle.js

    2. **REPL / exec'd code (no ``__file__``):** falls back to
       :func:`pathlib.Path.cwd` — the current working directory of the
       process. This matches the convention CLI tools use when resolving
       relative paths::

           >>> import os, shinyreact
           >>> os.chdir("/path/to/my-app")
           >>> shinyreact.page_react_dep(js_file="bundle.js")
           # source["subdir"] == "/path/to/my-app"
           # name == "my-app"

       The fallback is deliberate — call from any working directory and you
       get a predictable result. If you need a specific directory regardless
       of CWD, pass ``src_dir``.

    Args:
        src_dir: Directory containing the JS/CSS. Inferred from the calling
            frame when omitted (see above).
        js_file: Filename of the JS entry point, relative to ``src_dir``
            (default ``"ui.js"``). Attached only if the file exists.
        css_file: Filename of the CSS file, relative to ``src_dir`` (default
            ``"ui.css"``). Attached only if the file exists; ``None`` to skip.
        name: Dependency name. Defaults to ``src_dir``'s basename.
    """
    if src_dir is not None:
        base_dir = Path(src_dir)
    else:
        caller_file = sys._getframe(1).f_globals.get("__file__")
        # If the caller has no __file__ (REPL or dynamically exec'd code),
        # fall back to the current working directory — same convention as
        # most CLI tools resolving relative paths.
        base_dir = Path(caller_file).parent if caller_file else Path.cwd()
    dep_name = name if name is not None else base_dir.name

    js_path = base_dir / js_file
    mtime = _file_mtime_int(js_path)
    version = str(mtime) if mtime is not None else "0"

    script: ScriptItem | None = None
    if js_path.exists():
        script = {"src": js_file, "type": "module"}
    else:
        # An empty dependency loads nothing and reports nothing, so say so here
        # — without the tag there is not even a 404 in the console to go on.
        warnings.warn(
            f"JS entry point not found: {js_path}. No script tag will be "
            "emitted. Build the bundle first?",
            stacklevel=2,
        )

    stylesheet: StylesheetItem | None = None
    if css_file is not None and (base_dir / css_file).exists():
        stylesheet = {"href": css_file}

    return HTMLDependency(
        name=dep_name,
        version=version,
        source={"subdir": str(base_dir)},
        script=script,
        stylesheet=stylesheet,
    )


# Cache of documents read by page_react_html(), keyed by resolved path. Value is
# (stat signature, text).
_DOCUMENT_CACHE: dict[Path, tuple[tuple[int, int], str]] = {}


def _read_document_cached(path: Path) -> str:
    """Read an HTML document, re-reading only when it has changed on disk.

    ``ReactApp`` makes the UI a per-request function, so ``page_react_html()``
    runs on every page render. Reading the file each time is what lets an author
    edit ``index.html`` and hit refresh — no restart — but re-reading bytes that
    have not changed is pure waste on a page that never changes.

    So: stat every call, read only when the signature moves. ``st_mtime_ns`` plus
    ``st_size`` is the same heuristic build tools use; a same-nanosecond,
    same-size edit would be missed, which needs a machine fast enough to write
    twice within one filesystem timestamp tick.

    Not thread-locked deliberately: two concurrent requests may both read the
    file and both store the result, which costs one redundant read and cannot
    produce a wrong answer.
    """
    stat = path.stat()
    signature = (stat.st_mtime_ns, stat.st_size)
    cached = _DOCUMENT_CACHE.get(path)
    if cached is not None and cached[0] == signature:
        return cached[1]
    text = path.read_text(encoding="utf-8")
    _DOCUMENT_CACHE[path] = (signature, text)
    return text


def set_react_page(
    path: str | Path | None = None, *, shinyreact_js: ShinyreactJs = "server"
) -> None:
    """Set the page for this Express app to a React app (the ui.tsx pattern).

    With no arguments, serves ``www/index.html`` when it exists; otherwise
    falls back to :func:`page_react`-style discovery of ``www/ui.js`` /
    ``www/ui.css``, emitting no body HTML at all (your JS appends its own
    mount container to ``<body>``). Passing ``path`` explicitly requires the
    file to exist.

    When an HTML file is used, it is read once (cached at call time) and used
    as the page body. In both modes, dependencies from traditional Shiny
    renderers (e.g. ``@render.data_frame``) are discovered automatically and
    injected into the page head.

    Renderers defined inside ``@module.server`` are discovered too: every
    renderer mounted while the app body runs is found via the session's
    registered outputs, so module components load their JS/CSS with no extra
    configuration. Renderers mounted *dynamically after page load* (e.g. a
    module server called inside a ``@reactive.effect``) are not in the initial
    page; when their UI is delivered through Shiny's dynamic-UI path
    (``@render.ui``), Shiny injects their dependencies on render.

    .. note::

       Edits to ``index.html`` require restarting the Shiny server — see the
       comment in :func:`_build_react_page_fn` for the upstream Shiny Express
       constraint that prevents per-request re-reads.

    Path resolution
    ---------------
    ``path`` resolution depends on whether it is absolute or relative:

    1. **Absolute path:** used verbatim, regardless of caller or CWD::

           # /tmp/standalone-app.py
           from shinyreact import set_react_page
           set_react_page("/srv/myapp/www/index.html")
           # → reads /srv/myapp/www/index.html

    2. **Relative path from a module (typical):** resolved against the
       caller's module directory (read from the calling frame's
       ``__file__``)::

           # /path/to/my-app/app.py
           from shinyreact import set_react_page
           set_react_page()                    # → /path/to/my-app/www/index.html
           set_react_page("static/index.html") # → /path/to/my-app/static/index.html

       This is the expected usage for ``shiny run app.py``.

    3. **Relative path with no caller ``__file__`` (REPL / exec'd code):**
       falls back to :func:`pathlib.Path.cwd` — the current working
       directory of the process. Same convention CLI tools use for relative
       paths::

           >>> import os, shinyreact
           >>> os.chdir("/path/to/my-app")
           >>> shinyreact.set_react_page()        # → /path/to/my-app/www/index.html
           >>> shinyreact.set_react_page("a.html") # → /path/to/my-app/a.html

       The fallback is deliberate — call from any working directory and you
       get a predictable result. If you need a specific path regardless of
       CWD, pass an absolute path (case 1).

    Args:
        path: Path to the HTML file. Absolute paths are used verbatim;
            relative paths resolve against the caller module's directory,
            or against ``Path.cwd()`` when there is no caller ``__file__``.
            When ``None`` (the default), uses ``www/index.html`` if it
            exists, else discovers ``www/ui.js`` / ``www/ui.css``.
        shinyreact_js: Who supplies ``shinyreact.js`` / ``shinyreact.css``:
            ``"server"`` (default) or ``"client"`` for an npm-tier app whose
            bundle imports ``@posit/shinyreact`` — see :func:`page_react`.
    """
    # Validate now rather than at first page render: a typo should fail at
    # startup, next to the call that made it.
    _serves_bundle(shinyreact_js)
    caller_file = sys._getframe(1).f_globals.get("__file__")
    # If the caller has no __file__ (REPL or dynamically exec'd code),
    # fall back to the current working directory.
    caller_dir = Path(caller_file).parent if caller_file else Path.cwd()

    if path is None:
        index_path = caller_dir / "www" / "index.html"
        if not index_path.exists():
            page_opts(
                page_fn=_build_react_page_fn_discovered(caller_dir, shinyreact_js)
            )
            return
    else:
        path = Path(path)
        index_path = path if path.is_absolute() else caller_dir / path
    page_opts(page_fn=_build_react_page_fn(index_path, shinyreact_js))


def page_react_html(
    path: str | Path = "www/index.html",
    *,
    extra_deps: list[HTMLDependency] | None = None,
    shinyreact_js: ShinyreactJs = "server",
) -> ReactHtmlDocument:
    """Serve a React ``index.html`` document (the ui.tsx pattern, Core API).

    Reads a complete HTML document — the kind a Vite build emits — and injects
    Shiny's and shinyreact's dependencies into it. The document must contain
    Shiny's dependency placeholder in ``<head>``::

        <meta name="shiny-dependency-placeholder" content="">

    The script/link tags render in its place; the same literal is
    :attr:`shiny.ui.PageDocument.DEPS_PLACEHOLDER`. It is an ordinary ``<meta>``
    tag rather than template syntax, so the document stays valid HTML that a
    bundler's dev server can serve unchanged. Matches R's ``page_react_html()``.

    You rarely need to call this yourself — :class:`shinyreact.ReactApp`
    discovers ``www/index.html`` and calls it for you::

        from shinyreact import ReactApp

        app = ReactApp(server)

    Call it directly to pass a non-default path (``ReactApp(server,
    ui=page_react_html("client/index.html"))``). ``shiny.App`` works too (via
    ``ui.PageDocument``, py-shiny#2475), but only ``ReactApp`` mounts the
    document's directory at ``/``, so the assets the document references
    (your bundle's JS/CSS) are served when they live next to it
    (conventionally ``www/``).

    For apps that don't need to own the HTML document, prefer
    :func:`page_react` — it requires no HTML file at all and works with plain
    ``shiny.App``.

    Args:
        path: Path to the HTML document. Absolute paths are used verbatim;
            relative paths resolve against the caller module's directory, or
            against :func:`pathlib.Path.cwd` when there is no caller
            ``__file__``. Defaults to ``"www/index.html"``.
        extra_deps: Additional :class:`~htmltools.HTMLDependency` objects to
            render at the placeholder. A full document has no tag tree to
            attach dependencies to, so this is the only way in — the
            counterpart of :func:`page_react`'s positional ``*args``. They
            render *after* Shiny's and shinyreact's, so they can rely on
            ``window.shinyreact`` existing.
        shinyreact_js: Who supplies ``shinyreact.js`` / ``shinyreact.css``:
            ``"server"`` (default) or ``"client"`` for an npm-tier app whose
            bundle imports ``@posit/shinyreact`` — see :func:`page_react`.
    """
    path = Path(path)
    if path.is_absolute():
        index_path = path
    else:
        caller_file = sys._getframe(1).f_globals.get("__file__")
        # If the caller has no __file__ (REPL or dynamically exec'd code),
        # fall back to the current working directory.
        caller_dir = Path(caller_file).parent if caller_file else Path.cwd()
        index_path = caller_dir / path
    if not index_path.exists():
        raise FileNotFoundError(f"HTML file not found: {index_path}")
    # ui.PageDocument (py-shiny#2475) owns the placeholder: it prefixes Shiny's
    # own dependencies and raises at render time when the document has no
    # placeholder to insert them at. We only add shinyreact's bundle and the
    # #shinyreact-config tag.
    return ReactHtmlDocument(
        _read_document_cached(index_path),
        src_dir=index_path.parent,
        extra_deps=[
            *([_dep()] if _serves_bundle(shinyreact_js) else []),
            _config_script_tag(),
            *(extra_deps or []),
        ],
    )


def _collect_renderer_deps(renderer: Renderer, deps: list[HTMLDependency]) -> None:
    """Append a renderer's output-UI dependencies to ``deps``.

    Calls ``.tagify()`` first so dependencies that only materialize during
    tagification are resolved (a bare ``get_dependencies()`` on the untagified
    UI can miss them). The page function runs under the Express stub session,
    whose ``_process_ui`` is a no-op, so tagify — not ``session._process_ui`` —
    is the correct resolver here; the resolved deps are emitted into the page
    TagList, and Shiny registers their file routes when it renders the page.
    """
    ui = renderer.auto_output_ui()
    if isinstance(ui, (Tag, TagList)):
        deps.extend(ui.tagify().get_dependencies())


def _harvest_renderer_deps(args: tuple[Any, ...]) -> list[HTMLDependency]:
    """Collect HTMLDependencies from Express renderers for the page head.

    Looks at the top-level renderers Shiny Express hands to the page function,
    plus every renderer registered on the active session — including those
    defined inside ``@module.server``, which ``args`` never sees (issue #87).
    At the tagify pass the stub session already holds every synchronously
    mounted renderer in ``output._outputs``.
    """
    deps: list[HTMLDependency] = []
    for arg in args:
        if isinstance(arg, Renderer):
            _collect_renderer_deps(arg, deps)
    session = get_current_session()
    if session is not None:
        # `_outputs` is private; Shiny exposes no public API to iterate
        # registered outputs.
        for info in session.output._outputs.values():
            _collect_renderer_deps(info.renderer, deps)
    return deps


# The `page_opts()` options a React page can honor, mapped onto page_bare()'s
# (i.e. page_bootstrap()'s) parameters. Everything else page_auto() might
# forward describes a Bootstrap layout a bare React page does not have.
_SUPPORTED_PAGE_OPTS = ("title", "lang", "theme")


def _react_page_opts(kwargs: dict[str, Any], *, mode: str) -> dict[str, Any]:
    """Validate the options ``page_auto()`` forwards to our page function.

    ``page_opts()`` records its arguments and ``page_auto()`` splats them into
    whatever ``page_fn`` it resolved — ours. So a page function taking only
    ``*args`` raises ``TypeError: ... unexpected keyword argument 'title'`` from
    inside a private local, which tells an author nothing about what to do.
    Accept what the page can express, and name the rest.
    """
    unsupported = [k for k in kwargs if k not in _SUPPORTED_PAGE_OPTS]
    if unsupported:
        supported = ", ".join(_SUPPORTED_PAGE_OPTS)
        raise TypeError(
            f"page_opts({unsupported[0]}=...) is not supported by "
            f"set_react_page()'s {mode}: a React page has no Bootstrap layout "
            f"to apply it to. Supported page options: {supported}."
        )
    return {k: v for k, v in kwargs.items() if v is not None}


def _build_react_page_fn_discovered(
    app_dir: Path, shinyreact_js: ShinyreactJs = "server"
) -> Callable[..., Tag]:
    """Express page function for the no-HTML-file mode.

    Serves a :func:`page_react` page from ``app_dir/www`` with the same
    renderer-dependency discovery as the index.html mode.
    """

    def _react_page_fn(*args: Any, **kwargs: Any) -> Tag:
        # `title` here is a default, so `page_opts(title=...)` overrides it.
        opts = {"title": app_dir.name, **_react_page_opts(kwargs, mode="page")}
        return page_react(
            *_harvest_renderer_deps(args),
            src_dir=app_dir / "www",
            shinyreact_js=shinyreact_js,
            **opts,
        )

    return _react_page_fn


def _build_react_page_fn(
    index_path: Path, shinyreact_js: ShinyreactJs = "server"
) -> Callable[..., Tag]:
    if not index_path.exists():
        raise FileNotFoundError(f"HTML file not found: {index_path}")

    # `index.html` is read once at construction time and closed over.
    # See issue #82 (https://github.com/posit-dev/shinyreact/issues/82) for
    # why a per-request re-read can't be implemented from inside this package
    # alone:
    #
    # Shiny Express's `shiny/express/_run.py` calls `run_express(...).tagify()`
    # ONCE at app startup. The resulting `app_ui` is a static `RenderedHTML`
    # whose bytes are served verbatim for every `/` request (see
    # `shiny/_app.py` around `if callable(self.ui): ... else: ui = self.ui`).
    # Express only wraps `app_ui` in a per-request callable when
    # `app_opts(bookmark_store=...)` is set to something other than `"disable"`
    # — the only knob exposed today that flips static → callable.
    #
    # So this closure could re-read on mtime change all it wants; it's only
    # invoked once. A real fix needs an upstream py-shiny change adding an
    # opt-in for per-request `app_ui` independent of bookmarking. Until then,
    # editing `www/index.html` requires restarting the Shiny server.
    # Explicit encoding: the default follows the platform locale, so a document
    # with non-ASCII content would decode differently on a machine whose locale
    # is not UTF-8. R's page_react_html() decodes UTF-8 unconditionally.
    index_html = index_path.read_text(encoding="utf-8")

    def _react_page_fn(*args: Any, **kwargs: Any) -> Tag:
        if kwargs:
            # This mode emits no page tag at all — the document's own HTML is
            # the body — so there is nothing for title/lang/theme to land on.
            # Raise instead of ignoring, and instead of the bare TypeError that
            # page_auto()'s splat used to produce from inside this local.
            raise TypeError(
                f"page_opts({next(iter(kwargs))}=...) is not supported by "
                "set_react_page()'s HTML-file mode, which emits the document "
                "as the page body and no page tag of its own. Put it in the "
                "HTML, or use the no-HTML-file mode, which supports "
                f"{', '.join(_SUPPORTED_PAGE_OPTS)}."
            )
        deps = _harvest_renderer_deps(args)
        # Shiny de-duplicates dependencies by name+version when hoisting to
        # <head>, so any overlap between the harvest passes is harmless.
        # page_opts types page_fn as -> Tag, but TagList works at runtime
        return cast(Tag, TagList(_dep_page(shinyreact_js), *deps, HTML(index_html)))

    return _react_page_fn
