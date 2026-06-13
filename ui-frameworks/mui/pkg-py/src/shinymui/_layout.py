from __future__ import annotations

import shinyreact


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
