from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, cast

from htmltools import HTML, HTMLDependency, Tag, TagChild, TagList, tags
from shiny.express.ui import page_opts
from shiny.render.renderer import Renderer

from ._output import _dep


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

    Creates an HTML page with the shinyreact dependency and a ``#root`` div for
    mounting a React app. Shiny runs in the background for reactivity.

    Pass :class:`~htmltools.HTMLDependency` objects (e.g. from
    :func:`page_react_dep`) as positional arguments to include app JS/CSS.
    Shiny automatically hoists them to ``<head>``.

    Args:
        *args: HTMLDependency objects and/or child tags for the page.
        title: Page title.
        lang: HTML ``lang`` attribute.
    """
    return page_bare(
        _dep(),
        tags.div(id="root"),
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

    Resolves file paths relative to the **caller's** module directory and uses
    the JS file's mtime as the version for automatic cache-busting during
    development.

    Args:
        js_file: Filename of the JS entry point (default ``"main.js"``).
        css_file: Filename of the CSS file (default ``"main.css"``).
    """
    caller_file = sys._getframe(1).f_globals.get("__file__", "")
    src_dir = Path(caller_file).parent
    dep_name = src_dir.name

    js_path = src_dir / js_file
    version = str(int(js_path.stat().st_mtime)) if js_path.exists() else "0"

    return HTMLDependency(
        name=dep_name,
        version=version,
        source={"subdir": str(src_dir)},
        script={"src": js_file, "type": "module"},
        stylesheet={"href": css_file},
    )


def set_react_page(path: str | Path = "www/index.html") -> None:
    """Set the page for this Express app to an HTML file hosting a React app.

    Reads the specified HTML file (relative to the app file) and uses it as the
    page body. Dependencies from traditional Shiny renderers (e.g.
    ``@render.data_frame``) are discovered automatically and injected into the
    page head.

    Args:
        path: Path to the HTML file. If relative, resolved against the app
            file's directory. Defaults to ``"www/index.html"``.
    """
    caller_dir = Path(sys._getframe(1).f_globals.get("__file__", "")).parent
    index_path = caller_dir / Path(path)
    page_opts(page_fn=_build_react_page_fn(index_path))


def _build_react_page_fn(index_path: Path) -> Callable[..., Tag]:
    if not index_path.exists():
        raise FileNotFoundError(f"HTML file not found: {index_path}")
    index_html = index_path.read_text()

    def _react_page_fn(*args: Any) -> Tag:
        deps: list[HTMLDependency] = []
        for arg in args:
            if isinstance(arg, Renderer):
                ui = arg.auto_output_ui()
                if isinstance(ui, (Tag, TagList)):
                    deps.extend(ui.get_dependencies())

        # page_opts types page_fn as -> Tag, but TagList works at runtime
        return cast(Tag, TagList(_dep(), *deps, HTML(index_html)))

    return _react_page_fn
