from __future__ import annotations

from typing import TYPE_CHECKING

from htmltools import Tag, TagList, tags

if TYPE_CHECKING:
    pass


def _page_bare(
    *args: Tag | TagList | str,
    title: str | None = None,
    lang: str = "en",
) -> Tag:
    """Create a bare HTML page with only Shiny dependencies."""
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


def _page_react(
    *args: Tag | TagList | str,
    title: str | None = None,
    js_file: str = "main.js",
    css_file: str = "main.css",
    lang: str = "en",
) -> Tag:
    """Create a full-page React app served by Shiny.

    Internal function — not part of the public API. Creates an HTML page
    with a ``#root`` div, the specified JS/CSS files, and Shiny dependencies.

    Args:
        title: Page title.
        js_file: Path to the main JS bundle (served from static_assets).
        css_file: Path to the main CSS file (served from static_assets).
        lang: HTML lang attribute.
    """
    return _page_bare(
        tags.link(rel="stylesheet", href=css_file),
        tags.div(id="root"),
        *args,
        tags.script(src=js_file, type="module"),
        title=title,
        lang=lang,
    )
