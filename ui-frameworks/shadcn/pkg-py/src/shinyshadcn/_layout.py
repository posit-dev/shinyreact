from __future__ import annotations

from typing import Literal

import shinyreact


def card(
    *children: object,
    title: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A card container with an optional header title.

    Args:
        *children: Child nodes rendered inside the card body.
        title: Optional card header text.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Card",
        props={"title": title, "className": class_},
        children=list(children),
    )


def tab(value: str, label: str) -> dict[str, str]:
    """A single tab trigger spec for :func:`tabs`.

    Args:
        value: Identifier for this tab (matches the active-tab input value).
        label: Text shown on the tab trigger.
    """
    return {"value": value, "label": label}


def tabs(
    input_id: str,
    tabs: list[dict[str, str]],
    *panels: object,
    selected: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A tabbed panel. ``tabs`` defines the triggers; ``panels`` are the content.

    Panels are matched to tabs positionally — the Nth panel renders under the
    Nth tab. Server reads ``input.<input_id>()`` as the active tab's value.

    Args:
        input_id: Shiny input id for the active tab (two-way).
        tabs: Tab trigger specs, built with :func:`tab`.
        *panels: One content node per tab, in the same order as ``tabs``.
        selected: Initially active tab value (defaults to the first tab).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Tabs",
        props={
            "input_id": input_id,
            "tabs": tabs,
            "selected": selected,
            "className": class_,
        },
        children=list(panels),
    )


def collapsible(
    input_id: str,
    *children: object,
    trigger_label: str = "Toggle",
    open: bool = False,
    class_: str | None = None,
) -> shinyreact.Node:
    """A disclosure: a trigger reveals/hides its children. Server reads
    ``input.<input_id>()`` as a boolean (open).

    Args:
        input_id: Shiny input id.
        *children: Content shown when open.
        trigger_label: Label on the toggle button.
        open: Initial open state.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Collapsible",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "open": open,
            "className": class_,
        },
        children=list(children),
    )


def accordion_item(value: str, title: str) -> dict[str, str]:
    """An accordion section header for :func:`accordion` (value + title)."""
    return {"value": value, "title": title}


def accordion(
    input_id: str,
    items: list[dict[str, str]],
    *panels: object,
    type: Literal["single", "multiple"] = "single",
    selected: object | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A vertical accordion. ``items`` are the section headers; ``panels`` are the
    content, matched positionally. Server reads ``input.<input_id>()`` as the open
    value(s) — string for "single", list for "multiple".

    Args:
        input_id: Shiny input id.
        items: Section specs, built with :func:`accordion_item`.
        *panels: One content node per item, in the same order.
        type: "single" (one open) or "multiple".
        selected: Initially open value(s).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Accordion",
        props={
            "input_id": input_id,
            "items": items,
            "type": type,
            "selected": selected,
            "className": class_,
        },
        children=list(panels),
    )


def resizable(
    *children: object,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    panels: list[dict[str, object]] | None = None,
    handle: bool = True,
    class_: str | None = None,
) -> shinyreact.Node:
    """A resizable panel group. Children are placed in panels separated by drag handles.

    Args:
        *children: Content nodes — each goes into one resizable panel.
        orientation: "horizontal" (side-by-side) or "vertical" (stacked).
        panels: Optional list of ``{"default_size": %, "min_size": %}`` per panel.
        handle: Show the grip icon on the resize handle.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Resizable",
        props={
            "orientation": orientation,
            "panels": panels or [],
            "handle": handle,
            "className": class_,
        },
        children=list(children),
    )


def scroll_area(
    *children: object,
    height: str = "300px",
    orientation: Literal["vertical", "horizontal", "both"] = "vertical",
    class_: str | None = None,
) -> shinyreact.Node:
    """A scrollable container. Children are the scroll content.

    Args:
        *children: Content nodes rendered inside the scrollable area.
        height: CSS height string (e.g. ``"300px"``).
        orientation: "vertical", "horizontal", or "both".
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:ScrollArea",
        props={"height": height, "orientation": orientation, "className": class_},
        children=list(children),
    )
