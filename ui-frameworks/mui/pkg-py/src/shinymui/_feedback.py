from __future__ import annotations

from typing import Literal

import shinyreact


def backdrop(
    input_id: str,
    *children: object,
    class_: str | None = None,
) -> shinyreact.Node:
    """A dimming overlay. Server reads ``input.<input_id>()`` as the open state.

    Clicking the backdrop sets the input back to ``False``.

    Args:
        input_id: Shiny input id holding the boolean open state.
        *children: Content rendered on top of the overlay (e.g. a spinner).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:Backdrop",
        props={"input_id": input_id, "className": class_},
        children=list(children),
    )


def circular_progress(
    value: int | float | None = None,
    *,
    color: str = "primary",
    class_: str | None = None,
) -> shinyreact.Node:
    """A circular progress spinner. Display-only.

    Args:
        value: Fill percentage, 0–100. ``None`` renders an indeterminate spinner.
        color: Theme color (e.g. "primary", "secondary", "success").
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:CircularProgress",
        props={"value": value, "color": color, "className": class_},
    )


def linear_progress(
    value: int | float | None = None,
    *,
    color: str = "primary",
    class_: str | None = None,
) -> shinyreact.Node:
    """A linear progress bar. Display-only.

    Args:
        value: Fill percentage, 0–100. ``None`` renders an indeterminate bar.
        color: Theme color (e.g. "primary", "secondary", "success").
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:LinearProgress",
        props={"value": value, "color": color, "className": class_},
    )


def skeleton(
    *,
    variant: Literal["text", "rectangular", "rounded", "circular"] = "text",
    width: int | float | str | None = None,
    height: int | float | str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A loading placeholder shape shown while content loads. Display-only.

    Args:
        variant: Placeholder shape — "text", "rectangular", "rounded", or "circular".
        width: Placeholder width (pixels or CSS length).
        height: Placeholder height (pixels or CSS length).
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:Skeleton",
        props={
            "variant": variant,
            "width": width,
            "height": height,
            "className": class_,
        },
    )


def snackbar(
    input_id: str,
    *,
    message: str = "",
    auto_hide_ms: int = 4000,
    class_: str | None = None,
) -> shinyreact.Node:
    """A transient notification. Server reads ``input.<input_id>()`` as the open state.

    The snackbar sets the input back to ``False`` when it auto-hides or closes.

    Args:
        input_id: Shiny input id holding the boolean open state.
        message: Text shown in the snackbar.
        auto_hide_ms: Milliseconds before the snackbar auto-hides.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="mui:Snackbar",
        props={
            "input_id": input_id,
            "message": message,
            "auto_hide_ms": auto_hide_ms,
            "className": class_,
        },
    )
