from __future__ import annotations

import shinyreact


def box(
    *children: object,
    class_: str | None = None,
) -> shinyreact.Node:
    """An MUI Box — a generic container that wraps its children.

    Args:
        *children: Child nodes rendered inside the box.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:Box",
        props={"className": class_},
        children=list(children),
    )


def button_group(
    *children: object,
    variant: str = "contained",
    orientation: str = "horizontal",
    color: str = "primary",
    class_: str | None = None,
) -> shinyreact.Node:
    """An MUI ButtonGroup — groups child buttons together.

    Args:
        *children: Child buttons grouped together.
        variant: Button style ("contained", "outlined", "text").
        orientation: "horizontal" or "vertical".
        color: Theme color ("primary", "secondary", etc.).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:ButtonGroup",
        props={
            "variant": variant,
            "orientation": orientation,
            "color": color,
            "className": class_,
        },
        children=list(children),
    )


def container(
    *children: object,
    max_width: str = "md",
    class_: str | None = None,
) -> shinyreact.Node:
    """An MUI Container — centered, width-constrained layout wrapper.

    Args:
        *children: Child nodes rendered inside the container.
        max_width: Max width breakpoint ("xs", "sm", "md", "lg", "xl").
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:Container",
        props={"max_width": max_width, "className": class_},
        children=list(children),
    )


def grid(
    *children: object,
    spacing: int = 2,
    class_: str | None = None,
) -> shinyreact.Node:
    """An MUI Grid in container mode — lays out children on a grid.

    Args:
        *children: Child nodes placed within the grid.
        spacing: Gap between grid items (theme spacing units).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:Grid",
        props={"spacing": spacing, "className": class_},
        children=list(children),
    )


def stack(
    *children: object,
    direction: str = "column",
    spacing: int = 2,
    class_: str | None = None,
) -> shinyreact.Node:
    """An MUI Stack — lays out children along one axis.

    Args:
        *children: Child nodes stacked along the axis.
        direction: "column" (vertical) or "row" (horizontal).
        spacing: Gap between items (theme spacing units).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:Stack",
        props={"direction": direction, "spacing": spacing, "className": class_},
        children=list(children),
    )
