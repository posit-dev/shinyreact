from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, cast

from htmltools import HTML, HTMLDependency, Tag, TagChild, TagList, tags
from shiny.express.ui import page_opts
from shiny.render.renderer import Renderer

from ._output import _dep_page, _file_mtime_int


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

    head_content = TagList()
    if title:
        head_content = TagList(tags.title(title))

    return page_bootstrap(
        head_content,
        *args,
        title=title,
        lang=lang,
    )


def page_react(
    *args: TagChild,
    title: str | None = None,
    lang: str = "en",
) -> Tag:
    """Create a full-page React app served by Shiny.

    Creates an HTML page with the shinyreact dependency. Shiny runs in the
    background for reactivity.

    Pass :class:`~htmltools.HTMLDependency` objects (e.g. from
    :func:`page_react_dep`) as positional arguments to include app JS/CSS.
    Shiny automatically hoists them to ``<head>``.

    Args:
        *args: HTMLDependency objects and/or child tags for the page.
        title: Page title.
        lang: HTML ``lang`` attribute.
    """
    return page_bare(
        _dep_page(),
        *args,
        title=title,
        lang=lang,
    )


def page_react_dep(
    *,
    js_file: str = "main.js",
    css_file: str = "main.css",
) -> HTMLDependency:
    """Build an HTMLDependency for a React app's JS and CSS entry points.

    Resolves file paths relative to the caller's module directory (read from
    the calling frame's ``__file__``). The JS file's mtime is used as the
    dependency version for automatic cache-busting during development.

    Path resolution
    ---------------
    The base directory is determined as follows:

    1. **Module call (typical):** when the caller is a regular Python module
       (``__file__`` set), paths resolve against the module's directory. This
       is the expected usage::

           # /path/to/my-app/app.py
           from shinyreact import page_react, page_react_dep

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
       of CWD, ``chdir`` first or call from a real module file.

    Args:
        js_file: Filename of the JS entry point, relative to the resolved
            base directory (default ``"main.js"``).
        css_file: Filename of the CSS file, relative to the resolved base
            directory (default ``"main.css"``).
    """
    caller_file = sys._getframe(1).f_globals.get("__file__")
    # If the caller has no __file__ (REPL or dynamically exec'd code),
    # fall back to the current working directory — same convention as
    # most CLI tools resolving relative paths.
    src_dir = Path(caller_file).parent if caller_file else Path.cwd()
    dep_name = src_dir.name

    js_path = src_dir / js_file
    mtime = _file_mtime_int(js_path)
    version = str(mtime) if mtime is not None else "0"

    return HTMLDependency(
        name=dep_name,
        version=version,
        source={"subdir": str(src_dir)},
        script={"src": js_file, "type": "module"},
        stylesheet={"href": css_file},
    )


def set_react_page(path: str | Path = "www/index.html") -> None:
    """Set the page for this Express app to an HTML file hosting a React app.

    Reads the specified HTML file once (cached at call time) and uses it as
    the page body. Dependencies from traditional Shiny renderers (e.g.
    ``@render.data_frame``) are discovered automatically and injected into
    the page head.

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
        for arg in args:
            if isinstance(arg, Renderer):
                ui = arg.auto_output_ui()
                if isinstance(ui, (Tag, TagList)):
                    deps.extend(ui.get_dependencies())

        # page_opts types page_fn as -> Tag, but TagList works at runtime
        return cast(Tag, TagList(_dep_page(), *deps, HTML(index_html)))

    return _react_page_fn
