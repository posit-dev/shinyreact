from __future__ import annotations

from htmltools import Tag, TagChild, TagList, tags

from ._output import _dep


def page_bare(
    *args: TagChild,
    title: str | None = None,
    lang: str = "en",
) -> Tag:
    """Create a bare HTML page with only Shiny dependencies.

    This is the escape hatch for fully custom setups that don't need the
    shinyjson JS/CSS. It wraps ``shiny.ui.page_bootstrap()`` with minimal
    defaults.

    Args:
        *args: Child tags to include in the page body.
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
    js_file: str = "main.js",
    css_file: str = "main.css",
    lang: str = "en",
) -> Tag:
    """Create a full-page React app served by Shiny.

    Creates an HTML page with the shinyjson dependency, a ``#root`` div for
    mounting a React app, and ``<script>``/``<link>`` tags for the provided
    JS/CSS files. Shiny runs in the background for reactivity.

    Args:
        *args: Additional child tags to include in the page body.
        title: Page title.
        js_file: Path to the main JS bundle.
        css_file: Path to the main CSS file.
        lang: HTML ``lang`` attribute.
    """
    # TODO: Accept extra_deps: list[HTMLDependency] instead of / in addition
    # to js_file/css_file string paths.
    return page_bare(
        _dep(),
        tags.link(rel="stylesheet", href=css_file),
        tags.div(id="root"),
        *args,
        tags.script(src=js_file, type="module"),
        title=title,
        lang=lang,
    )
