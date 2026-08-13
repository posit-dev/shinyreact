from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, cast

from htmltools import HTML, HTMLDependency, Tag, TagChild, TagList
from shiny.express.ui import page_opts
from shiny.render.renderer import Renderer
from shiny.session import get_current_session

from ._dep import _dep_page, _file_mtime_int

if TYPE_CHECKING:
    # Private, but it is the only name for HTMLDependency's stylesheet entry.
    from htmltools._core import ScriptItem, StylesheetItem


def page_bare(
    *args: TagChild,
    title: str | None = None,
    lang: str = "en",
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
    """
    from shiny.ui import page_bootstrap

    return page_bootstrap(
        *args,
        title=title,
        lang=lang,
    )


def page_react_dep(
    *,
    src_dir: str | Path | None = None,
    js_file: str = "main.js",
    css_file: str | None = "main.css",
    name: str | None = None,
) -> HTMLDependency:
    """Build an HTMLDependency for a React app's JS and CSS entry points.

    The JS file's mtime is used as the dependency version for automatic
    cache-busting during development.

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
            (default ``"main.js"``). Attached only if the file exists.
        css_file: Filename of the CSS file, relative to ``src_dir`` (default
            ``"main.css"``). Attached only if the file exists; ``None`` to skip.
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


def set_react_page(path: str | Path = "www/index.html") -> None:
    """Set the page for this Express app to an HTML file hosting a React app.

    Reads the specified HTML file once (cached at call time) and uses it as
    the page body. Dependencies from traditional Shiny renderers (e.g.
    ``@render.data_frame``) are discovered automatically and injected into
    the page head.

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
            Defaults to ``"www/index.html"``.
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
    page_opts(page_fn=_build_react_page_fn(index_path))


def page_react_html(path: str | Path = "www/index.html") -> TagList:
    """Serve a static React ``index.html`` (the ui.tsx pattern, Core API).

    The Core-mode counterpart to :func:`set_react_page`. Reads an HTML file,
    attaches the shinyreact page-level dependency, and returns UI suitable for
    use as the ``ui`` argument of :class:`shiny.App`. Use this when you write a
    Core-style app (``App(app_ui, server)``); use :func:`set_react_page` for
    Shiny Express apps.

    Unlike :func:`set_react_page`, this does not auto-discover dependencies
    from traditional Shiny renderers — it only attaches the shinyreact bundle.

    Args:
        path: Path to the HTML file. Absolute paths are used verbatim;
            relative paths resolve against the caller module's directory, or
            against :func:`pathlib.Path.cwd` when there is no caller
            ``__file__``. Defaults to ``"www/index.html"``.
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
    index_html = index_path.read_text()
    return TagList(_dep_page(), HTML(index_html))


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


def _build_react_page_fn(index_path: Path) -> Callable[..., Tag]:
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
    index_html = index_path.read_text()

    def _react_page_fn(*args: Any) -> Tag:
        deps: list[HTMLDependency] = []

        # Top-level renderers Shiny Express hands to the page function.
        for arg in args:
            if isinstance(arg, Renderer):
                _collect_renderer_deps(arg, deps)

        # Renderers registered on the active session — including those defined
        # inside @module.server, which `*args` never sees (issue #87). At the
        # tagify pass the stub session already holds every synchronously
        # mounted renderer in `output._outputs`.
        session = get_current_session()
        if session is not None:
            # `_outputs` is private; Shiny exposes no public API to iterate
            # registered outputs.
            for info in session.output._outputs.values():
                _collect_renderer_deps(info.renderer, deps)

        # Shiny de-duplicates dependencies by name+version when hoisting to
        # <head>, so any overlap between the two passes is harmless.
        # page_opts types page_fn as -> Tag, but TagList works at runtime
        return cast(Tag, TagList(_dep_page(), *deps, HTML(index_html)))

    return _react_page_fn
