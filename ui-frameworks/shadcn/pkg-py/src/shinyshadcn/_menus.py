from __future__ import annotations

from typing import Literal

import shinyreact


def menu_item(
    value: str,
    label: str,
    *,
    disabled: bool = False,
    variant: Literal["default", "destructive"] = "default",
) -> dict[str, object]:
    """A clickable menu action. Clicking it fires the menu's ``input_id``.

    Args:
        value: Identifier reported to the server when this item is clicked.
        label: Text shown in the menu.
        disabled: Greys the item out and blocks clicks.
        variant: "default" or "destructive" (red, for delete-style actions).
    """
    return {
        "type": "item",
        "value": value,
        "label": label,
        "disabled": disabled,
        "variant": variant,
    }


def menu_label(label: str) -> dict[str, object]:
    """A non-interactive section header inside a menu."""
    return {"type": "label", "label": label}


def menu_separator() -> dict[str, object]:
    """A divider line between menu sections."""
    return {"type": "separator"}


def menu_checkbox(
    input_id: str,
    label: str,
    *,
    checked: bool = False,
) -> dict[str, object]:
    """A toggleable menu item with its own boolean Shiny input.

    Unlike :func:`menu_item` (an event), a checkbox holds persistent state.
    Server reads ``input.<input_id>()`` as a boolean.

    Args:
        input_id: Shiny input id for this checkbox's state.
        label: Text shown beside the checkmark.
        checked: Initial checked state.
    """
    return {
        "type": "checkbox",
        "input_id": input_id,
        "label": label,
        "checked": checked,
    }


def menu_submenu(label: str, *items: dict[str, object]) -> dict[str, object]:
    """A nested submenu. ``items`` are more menu_* builders (recursive).

    Args:
        label: Text on the submenu trigger row.
        *items: The submenu's contents.
    """
    return {"type": "submenu", "label": label, "items": list(items)}


def dropdown_menu(
    input_id: str,
    *items: dict[str, object],
    trigger_label: str = "Open",
    class_: str | None = None,
) -> shinyreact.Node:
    """A dropdown menu driven by an ``items`` data array.

    Clicking a :func:`menu_item` sets ``input.<input_id>()`` to a dict
    ``{"value": ..., "nonce": ...}`` — the nonce changes on every click so that
    clicking the same item twice still registers as a new event. Pair with
    ``@reactive.event(input.<input_id>, ignore_init=True)`` on the server.

    Args:
        input_id: Shiny input id for click events.
        *items: Menu contents, built with the ``menu_*`` helpers.
        trigger_label: Label on the button that opens the menu.
        class_: Extra CSS classes merged onto the menu content panel.
    """
    return shinyreact.Node(
        type="shadcn:DropdownMenu",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "items": list(items),
            "className": class_,
        },
    )


def context_menu(
    input_id: str,
    *children: object,
    items: list[dict[str, object]] | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A right-click context menu. Children = the trigger area; items = menu contents.

    Clicking a menu item sets ``input.<input_id>()`` to ``{"value": ..., "nonce": ...}``
    (nonce changes on every click so repeated clicks still register).
    Use the same ``menu_item``/``menu_label``/``menu_separator`` helpers as
    :func:`dropdown_menu`.

    Args:
        input_id: Shiny input id for click events.
        *children: The area the user right-clicks on.
        items: Menu contents built with the ``menu_*`` helpers.
        class_: Extra CSS classes merged onto the trigger wrapper.
    """
    return shinyreact.Node(
        type="shadcn:ContextMenu",
        props={"input_id": input_id, "items": items or [], "className": class_},
        children=list(children),
    )


def menubar_menu(label: str, *items: dict[str, object]) -> dict[str, object]:
    """A single menu in a :func:`menubar` (label + items).

    Args:
        label: Text shown on the menu trigger in the bar.
        *items: Menu items built with the ``menu_*`` helpers.
    """
    return {"label": label, "items": list(items)}


def menubar(
    input_id: str,
    *menus: dict[str, object],
    class_: str | None = None,
) -> shinyreact.Node:
    """A horizontal menu bar. Clicking an item sets ``input.<input_id>()`` to
    ``{"menu": ..., "value": ..., "nonce": ...}``.

    Args:
        input_id: Shiny input id for click events.
        *menus: Menu specs built with :func:`menubar_menu`.
        class_: Extra CSS classes merged onto the bar element.
    """
    return shinyreact.Node(
        type="shadcn:Menubar",
        props={"input_id": input_id, "menus": list(menus), "className": class_},
    )


def nav_item(
    label: str,
    href: str | None = None,
    *,
    description: str | None = None,
    items: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """A navigation item for :func:`navigation_menu`.

    Args:
        label: Text shown on the nav trigger.
        href: Link URL for plain links (omit for dropdown triggers).
        description: Optional description shown in sub-item dropdowns.
        items: Sub-items (makes this a dropdown trigger, not a plain link).
    """
    d: dict[str, object] = {"label": label}
    if href is not None:
        d["href"] = href
    if description is not None:
        d["description"] = description
    if items is not None:
        d["items"] = items
    return d


def navigation_menu(
    *items: dict[str, object],
    input_id: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A horizontal navigation bar. Data-driven from an ``items`` array.

    If ``input_id`` is provided, clicking a link fires ``input.<input_id>()``
    as ``{"value": label, "nonce": ...}`` instead of navigating.

    Args:
        *items: Nav items built with :func:`nav_item`.
        input_id: Optional Shiny input id for click tracking.
        class_: Extra CSS classes merged onto the nav root.
    """
    return shinyreact.Node(
        type="shadcn:NavigationMenu",
        props={"items": list(items), "input_id": input_id, "className": class_},
    )
