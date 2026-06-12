from __future__ import annotations

from typing import Literal

import shinyreact


def dialog(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    title: str | None = None,
    description: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A modal dialog. Server reads ``input.<input_id>()`` as bool (open state).

    Args:
        input_id: Shiny input id — ``True`` while the dialog is open.
        *children: Content nodes rendered inside the dialog body.
        trigger_label: Label on the button that opens the dialog.
        title: Optional dialog title.
        description: Optional muted subtitle shown below the title.
        class_: Extra CSS classes merged onto the dialog content panel.
    """
    return shinyreact.Node(
        type="shadcn:Dialog",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "title": title,
            "description": description,
            "className": class_,
        },
        children=list(children),
    )


def popover(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    align: Literal["start", "center", "end"] = "center",
    class_: str | None = None,
) -> shinyreact.Node:
    """A floating popover. Server reads ``input.<input_id>()`` as bool (open state).

    Args:
        input_id: Shiny input id — ``True`` while the popover is open.
        *children: Content nodes rendered inside the popover.
        trigger_label: Label on the button that opens the popover.
        align: Horizontal alignment of the panel relative to the trigger.
        class_: Extra CSS classes merged onto the popover content panel.
    """
    return shinyreact.Node(
        type="shadcn:Popover",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "align": align,
            "className": class_,
        },
        children=list(children),
    )


def drawer(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    direction: Literal["bottom", "top", "right", "left"] = "bottom",
    title: str | None = None,
    description: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A swipe drawer (vaul). Slides in from an edge; server reads open state as bool.

    Args:
        input_id: Shiny input id — ``True`` while the drawer is open.
        *children: Content nodes rendered inside the drawer.
        trigger_label: Label on the button that opens the drawer.
        direction: Edge the drawer slides from — "bottom", "top", "right", or "left".
        title: Optional drawer header title.
        description: Optional muted description below the title.
        class_: Extra CSS classes merged onto the drawer content panel.
    """
    return shinyreact.Node(
        type="shadcn:Drawer",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "direction": direction,
            "title": title,
            "description": description,
            "className": class_,
        },
        children=list(children),
    )


def alert_dialog(
    confirm_id: str,
    *,
    cancel_id: str | None = None,
    trigger_label: str = "Open",
    title: str = "Are you sure?",
    description: str | None = None,
    confirm_label: str = "Continue",
    cancel_label: str = "Cancel",
    class_: str | None = None,
) -> shinyreact.Node:
    """A confirmation dialog. Server reads ``input.<confirm_id>()`` as a click counter.

    Args:
        confirm_id: Shiny input id incremented when the user confirms.
        cancel_id: Optional Shiny input id incremented on cancel.
            If omitted, cancel just closes the dialog without firing.
        trigger_label: Label on the button that opens the dialog.
        title: Dialog title.
        description: Optional muted description text.
        confirm_label: Label on the confirm button.
        cancel_label: Label on the cancel button.
        class_: Extra CSS classes merged onto the dialog content panel.
    """
    return shinyreact.Node(
        type="shadcn:AlertDialog",
        props={
            "confirm_id": confirm_id,
            "cancel_id": cancel_id,
            "trigger_label": trigger_label,
            "title": title,
            "description": description,
            "confirm_label": confirm_label,
            "cancel_label": cancel_label,
            "className": class_,
        },
    )


def sheet(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    side: Literal["right", "left", "top", "bottom"] = "right",
    title: str | None = None,
    description: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A side-panel sheet. Server reads ``input.<input_id>()`` as bool (open state).

    Args:
        input_id: Shiny input id — ``True`` while the sheet is open.
        *children: Content nodes rendered inside the sheet.
        trigger_label: Label on the button that opens the sheet.
        side: Edge the sheet slides in from — "right", "left", "top", or "bottom".
        title: Optional sheet header title.
        description: Optional muted description below the title.
        class_: Extra CSS classes merged onto the sheet content panel.
    """
    return shinyreact.Node(
        type="shadcn:Sheet",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "side": side,
            "title": title,
            "description": description,
            "className": class_,
        },
        children=list(children),
    )
