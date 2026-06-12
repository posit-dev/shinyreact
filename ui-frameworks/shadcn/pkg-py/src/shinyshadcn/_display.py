from __future__ import annotations

from typing import Literal

import shinyreact

from ._types import BadgeVariant


def badge(
    text: str,
    *,
    variant: BadgeVariant = "default",
    class_: str | None = None,
) -> shinyreact.Node:
    """Display a small status badge.

    Args:
        text: Badge label text.
        variant: Visual style — default, secondary, destructive, outline, ghost, link.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Badge",
        props={"text": text, "variant": variant, "className": class_},
    )


def separator(
    *,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    class_: str | None = None,
) -> shinyreact.Node:
    """A thin rule line for visual separation.

    Args:
        orientation: "horizontal" (full-width line) or "vertical" (full-height line).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Separator",
        props={"orientation": orientation, "className": class_},
    )


def alert(
    description: str,
    *,
    title: str | None = None,
    variant: Literal["default", "destructive"] = "default",
    class_: str | None = None,
) -> shinyreact.Node:
    """A status alert box. Display-only — no Shiny input.

    Args:
        description: Alert body text.
        title: Optional bold title shown above the description.
        variant: "default" (neutral) or "destructive" (red, for errors/warnings).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Alert",
        props={
            "title": title,
            "description": description,
            "variant": variant,
            "className": class_,
        },
    )


def table(
    columns: list[str],
    rows: list[list[object]],
    *,
    caption: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A display-only data table. No Shiny input.

    Args:
        columns: Header labels.
        rows: Each row is a list of cell values (strings or numbers).
        caption: Optional caption shown below the table.
        class_: Extra CSS classes merged onto the table element.
    """
    return shinyreact.Node(
        type="shadcn:Table",
        props={
            "columns": columns,
            "rows": rows,
            "caption": caption,
            "className": class_,
        },
    )


def label(text: str, *, class_: str | None = None) -> shinyreact.Node:
    """A display-only text label.

    Args:
        text: Label text.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Label",
        props={"text": text, "className": class_},
    )


def skeleton(*, class_: str | None = None) -> shinyreact.Node:
    """A loading placeholder. Size it via ``class_`` (e.g. ``"h-4 w-32"``).

    Args:
        class_: CSS classes setting the placeholder's size/shape.
    """
    return shinyreact.Node(
        type="shadcn:Skeleton",
        props={"className": class_},
    )


def progress(
    value: int | float = 0,
    *,
    class_: str | None = None,
) -> shinyreact.Node:
    """A determinate progress bar. Display-only.

    Args:
        value: Fill percentage, 0–100.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Progress",
        props={"value": value, "className": class_},
    )


def avatar(
    *,
    src: str | None = None,
    fallback: str = "",
    size: Literal["default", "sm", "lg"] = "default",
    class_: str | None = None,
) -> shinyreact.Node:
    """A user avatar. Shows ``src`` if it loads, else the ``fallback`` initials.

    Args:
        src: Image URL (optional).
        fallback: Text shown when there's no image (usually initials).
        size: "default", "sm", or "lg".
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Avatar",
        props={"src": src, "fallback": fallback, "size": size, "className": class_},
    )


def crumb(label: str, href: str | None = None) -> dict[str, str]:
    """A breadcrumb item for :func:`breadcrumb` (label + optional href)."""
    return {"label": label, "href": href}


def breadcrumb(
    *items: dict[str, str],
    class_: str | None = None,
) -> shinyreact.Node:
    """A breadcrumb trail. Display-only.

    Args:
        *items: Items built with :func:`crumb`; the last is the current page.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Breadcrumb",
        props={"items": list(items), "className": class_},
    )


def kbd(text: str, *, class_: str | None = None) -> shinyreact.Node:
    """A keyboard-key hint. Display-only.

    Args:
        text: The key label (e.g. "⌘K").
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(type="shadcn:Kbd", props={"text": text, "className": class_})


def spinner(*, class_: str | None = None) -> shinyreact.Node:
    """A loading spinner. Size it via ``class_`` (e.g. ``"size-6"``). Display-only.

    Args:
        class_: CSS classes setting the spinner's size.
    """
    return shinyreact.Node(type="shadcn:Spinner", props={"className": class_})


def aspect_ratio(
    *children: object,
    ratio: int | float = 1.0,
    class_: str | None = None,
) -> shinyreact.Node:
    """A fixed aspect-ratio container.

    Args:
        *children: Content rendered inside (e.g. an image).
        ratio: Width / height (e.g. ``16 / 9``).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:AspectRatio",
        props={"ratio": ratio, "className": class_},
        children=list(children),
    )


def chart_series(
    key: str,
    *,
    label: str | None = None,
    color: str | None = None,
) -> dict[str, object]:
    """A data series spec for :func:`chart`.

    Args:
        key: Column name in the data dicts.
        label: Display name shown in legend/tooltip.
        color: CSS color (e.g. ``"#4f46e5"`` or ``"hsl(221 83% 53%)``").
    """
    return {"key": key, "label": label, "color": color}


def chart(
    data: list[dict[str, object]],
    series: list[dict[str, object]],
    *,
    type: Literal["bar", "line", "area", "pie"] = "bar",
    x_key: str = "name",
    height: int = 300,
    legend: bool = True,
    grid: bool = True,
    class_: str | None = None,
) -> shinyreact.Node:
    """A recharts chart. Display-only — no Shiny input.

    Args:
        data: List of row dicts, e.g. ``[{"month": "Jan", "sales": 120}, ...]``.
        series: Series specs built with :func:`chart_series`.
        type: Chart type — "bar", "line", "area", or "pie".
        x_key: Data key used as x-axis labels (or pie slice names).
        height: Chart height in pixels.
        legend: Show the legend.
        grid: Show the cartesian grid (ignored for pie).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Chart",
        props={
            "type": type,
            "data": data,
            "series": series,
            "x_key": x_key,
            "height": height,
            "legend": legend,
            "grid": grid,
            "className": class_,
        },
    )


def tooltip(
    *children: object,
    content: str = "",
    side: Literal["top", "right", "bottom", "left"] = "top",
    class_: str | None = None,
) -> shinyreact.Node:
    """A hover tooltip. Children = the trigger element; ``content`` = tooltip text.

    Args:
        *children: The element(s) the user hovers over to see the tooltip.
        content: Text shown in the tooltip bubble.
        side: Which side the tooltip appears on.
        class_: Extra CSS classes merged onto the tooltip content.
    """
    return shinyreact.Node(
        type="shadcn:Tooltip",
        props={"content": content, "side": side, "className": class_},
        children=list(children),
    )


def hover_card(
    *children: object,
    trigger_label: str = "Hover",
    side: Literal["top", "right", "bottom", "left"] = "bottom",
    align: Literal["start", "center", "end"] = "center",
    class_: str | None = None,
) -> shinyreact.Node:
    """A hover card. Children = card body; ``trigger_label`` = the trigger text.

    Args:
        *children: Content nodes rendered inside the card panel.
        trigger_label: Text shown as the hover trigger link.
        side: Which side the card appears on.
        align: Horizontal alignment of the card relative to the trigger.
        class_: Extra CSS classes merged onto the card content panel.
    """
    return shinyreact.Node(
        type="shadcn:HoverCard",
        props={
            "trigger_label": trigger_label,
            "side": side,
            "align": align,
            "className": class_,
        },
        children=list(children),
    )


def empty(
    *children: object,
    title: str | None = None,
    description: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """An empty-state placeholder. Children are rendered as the action area.

    Args:
        *children: Action nodes (e.g. a button) shown below the header.
        title: Bold heading text for the empty state.
        description: Muted description text below the title.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Empty",
        props={
            "title": title,
            "description": description,
            "className": class_,
        },
        children=list(children),
    )
