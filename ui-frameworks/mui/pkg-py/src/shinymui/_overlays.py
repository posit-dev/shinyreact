from __future__ import annotations

import shinyreact


def dialog(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    title: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A modal dialog. Server reads ``input.<input_id>()`` as the boolean open state.

    Args:
        input_id: Shiny input id tracking the open state.
        *children: Child nodes rendered in the dialog body.
        trigger_label: Text on the button that opens the dialog.
        title: Optional dialog title.
        class_: Extra CSS classes on the dialog root.
    """
    return shinyreact.Node(
        type="mui:Dialog",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "title": title,
            "className": class_,
        },
        children=list(children),
    )


def drawer(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    anchor: str = "left",
    class_: str | None = None,
) -> shinyreact.Node:
    """A sliding drawer. Server reads ``input.<input_id>()`` as the boolean open state.

    Args:
        input_id: Shiny input id tracking the open state.
        *children: Child nodes rendered inside the drawer.
        trigger_label: Text on the button that opens the drawer.
        anchor: Edge the drawer slides from — "left", "right", "top", or "bottom".
        class_: Extra CSS classes on the drawer root.
    """
    return shinyreact.Node(
        type="mui:Drawer",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "anchor": anchor,
            "className": class_,
        },
        children=list(children),
    )


def menu(
    input_id: str,
    items: object,
    *,
    trigger_label: str = "Open",
    class_: str | None = None,
) -> shinyreact.Node:
    """A dropdown menu. Server reads ``input.<input_id>()`` as ``{value, nonce}``.

    Args:
        input_id: Shiny input id for click events.
        items: List of menu entries, each with ``value`` and ``label`` keys.
        trigger_label: Text on the button that opens the menu.
        class_: Extra CSS classes on the menu root.
    """
    return shinyreact.Node(
        type="mui:Menu",
        props={
            "input_id": input_id,
            "items": items,
            "trigger_label": trigger_label,
            "className": class_,
        },
    )


def speed_dial(
    input_id: str,
    actions: object,
    *,
    class_: str | None = None,
) -> shinyreact.Node:
    """A floating speed-dial. Server reads ``input.<input_id>()`` as ``{value, nonce}``.

    Args:
        input_id: Shiny input id for click events.
        actions: List of action entries, each with ``value`` and ``label`` keys.
        class_: Extra CSS classes on the speed-dial root.
    """
    return shinyreact.Node(
        type="mui:SpeedDial",
        props={
            "input_id": input_id,
            "actions": actions,
            "className": class_,
        },
    )
