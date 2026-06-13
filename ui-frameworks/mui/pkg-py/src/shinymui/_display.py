from __future__ import annotations

from typing import Literal

import shinyreact


def alert(
    text: str,
    *,
    severity: Literal["error", "warning", "info", "success"] = "info",
    variant: Literal["standard", "filled", "outlined"] = "standard",
    class_: str | None = None,
) -> shinyreact.Node:
    """A status message. Display-only.

    Args:
        text: Message text.
        severity: Alert severity (controls color/icon).
        variant: MUI alert variant.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Alert",
        props={
            "text": text,
            "severity": severity,
            "variant": variant,
            "className": class_,
        },
    )


def avatar(
    *,
    src: str | None = None,
    alt: str | None = None,
    text: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """An avatar with an optional image, alt text, and fallback text.

    Args:
        src: Image URL (optional).
        alt: Alternate text for the image.
        text: Fallback text shown when there's no image (usually initials).
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Avatar",
        props={"src": src, "alt": alt, "text": text, "className": class_},
    )


def badge(
    *children: object,
    badge_content: object = None,
    color: Literal[
        "default", "primary", "secondary", "error", "info", "success", "warning"
    ] = "primary",
    class_: str | None = None,
) -> shinyreact.Node:
    """Overlays a small badge on its children.

    Args:
        *children: The element(s) the badge is overlaid on.
        badge_content: Content displayed inside the badge (e.g. a count).
        color: Badge color.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Badge",
        props={"badge_content": badge_content, "color": color, "className": class_},
        children=list(children),
    )


def breadcrumbs(
    items: list[dict[str, object]],
    *,
    class_: str | None = None,
) -> shinyreact.Node:
    """A static breadcrumb trail from {label, href} items. Display-only.

    Args:
        items: List of dicts with ``label`` and optional ``href``; the last is
            the current page.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Breadcrumbs",
        props={"items": items, "className": class_},
    )


def chip(
    label: str,
    *,
    color: Literal[
        "default", "primary", "secondary", "error", "info", "success", "warning"
    ] = "default",
    variant: Literal["filled", "outlined"] = "filled",
    class_: str | None = None,
) -> shinyreact.Node:
    """A compact label/tag chip. Display-only.

    Args:
        label: Chip text.
        color: Chip color.
        variant: MUI chip variant.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Chip",
        props={
            "label": label,
            "color": color,
            "variant": variant,
            "className": class_,
        },
    )


def divider(
    *,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    text: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A separator line, optionally with inline text. Display-only.

    Args:
        orientation: "horizontal" or "vertical".
        text: Optional inline text shown within the divider.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Divider",
        props={"orientation": orientation, "text": text, "className": class_},
    )


def image_list(
    items: list[dict[str, object]],
    *,
    cols: int = 3,
    class_: str | None = None,
) -> shinyreact.Node:
    """A data-driven grid of images. Display-only.

    Args:
        items: List of dicts with ``src`` and optional ``alt``.
        cols: Number of columns in the grid.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:ImageList",
        props={"items": items, "cols": cols, "className": class_},
    )


def link(
    label: str,
    href: str,
    *,
    target: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A static link. Display-only.

    Args:
        label: Link text.
        href: Destination URL.
        target: Anchor target (e.g. ``"_blank"``).
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Link",
        props={"label": label, "href": href, "target": target, "className": class_},
    )


def list(
    items: list[object],
    *,
    input_id: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A list of items. With ``input_id`` the items become clickable.

    Args:
        items: List of strings, or dicts with ``primary`` and optional
            ``secondary``.
        input_id: When set, items become clickable and the server reads the
            selected item via ``input.<input_id>()``.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:List",
        props={"input_id": input_id, "items": items, "className": class_},
    )


def stepper(
    steps: list[str],
    *,
    active: int = 0,
    class_: str | None = None,
) -> shinyreact.Node:
    """A static stepper from an array of step labels. Display-only.

    Args:
        steps: Step label strings.
        active: Zero-based index of the active step.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Stepper",
        props={"steps": steps, "active": active, "className": class_},
    )


def table(
    columns: list[str],
    rows: list[list[object]],
    *,
    class_: str | None = None,
) -> shinyreact.Node:
    """A static table from columns (header strings) and rows (arrays).

    Args:
        columns: Header labels.
        rows: Each row is a list of cell values.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Table",
        props={"columns": columns, "rows": rows, "className": class_},
    )


def tooltip(
    *children: object,
    title: str = "",
    class_: str | None = None,
) -> shinyreact.Node:
    """Wraps children with a hover tooltip.

    Args:
        *children: The element(s) the user hovers over to see the tooltip.
        title: Text shown in the tooltip bubble.
        class_: Extra CSS classes on the wrapping element.
    """
    return shinyreact.Node(
        type="mui:Tooltip",
        props={"title": title, "className": class_},
        children=list(children),
    )


def typography(
    text: str,
    *,
    variant: str = "body1",
    align: str | None = None,
    color: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """Text rendered with an MUI typography variant. Display-only.

    Args:
        text: Text content.
        variant: MUI typography variant (e.g. "h1", "body1").
        align: Text alignment (e.g. "left", "center", "right").
        color: Text color.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Typography",
        props={
            "text": text,
            "variant": variant,
            "align": align,
            "color": color,
            "className": class_,
        },
    )
