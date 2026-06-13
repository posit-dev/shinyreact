from __future__ import annotations

import shinyreact


def accordion_item(value: str, title: str) -> dict[str, str]:
    """An accordion section header for :func:`accordion` (value + title)."""
    return {"value": value, "title": title}


def accordion(
    items: list[dict[str, str]],
    *children: object,
    class_: str | None = None,
) -> shinyreact.Node:
    """A vertical accordion. ``items`` are the section headers; ``children`` are
    the panel bodies, matched positionally.

    Args:
        items: Section specs, built with :func:`accordion_item`.
        *children: One panel body per item, in the same order.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Accordion",
        props={"items": items, "className": class_},
        children=list(children),
    )


def app_bar(
    *children: object,
    title: str | None = None,
    position: str = "static",
    class_: str | None = None,
) -> shinyreact.Node:
    """A top app bar with an optional title and trailing children.

    Args:
        *children: Child nodes rendered in the toolbar.
        title: Optional title text.
        position: AppBar position (e.g. ``"static"``, ``"fixed"``).
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:AppBar",
        props={"title": title, "position": position, "className": class_},
        children=list(children),
    )


def card(
    *children: object,
    title: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A card container with an optional header title.

    Args:
        *children: Child nodes rendered in the card body.
        title: Optional header title.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Card",
        props={"title": title, "className": class_},
        children=list(children),
    )


def paper(
    *children: object,
    elevation: int = 1,
    class_: str | None = None,
) -> shinyreact.Node:
    """A Paper surface wrapping its children.

    Args:
        *children: Child nodes rendered on the surface.
        elevation: Shadow depth of the surface.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Paper",
        props={"elevation": elevation, "className": class_},
        children=list(children),
    )
