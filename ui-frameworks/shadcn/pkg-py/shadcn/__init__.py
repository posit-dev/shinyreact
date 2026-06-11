from __future__ import annotations

from pathlib import Path
from typing import Literal, Union

import shinyreact
from htmltools import HTMLDependency

_www = Path(__file__).parent.parent.parent / "www"


def _dep() -> HTMLDependency:
    js = _www / "shadcn.js"
    version = str(int(js.stat().st_mtime)) if js.exists() else "0"
    return HTMLDependency(
        name="shinyshadcn",
        version=version,
        source={"subdir": str(_www)},
        script={"src": "shadcn.js", "defer": ""},
        stylesheet={"href": "style.css"},
    )


def badge(
    text: str,
    *,
    variant: Literal["default", "secondary", "outline"] = "default",
) -> shinyreact.Node:
    """Display a small status badge.

    Args:
        text: Badge label text.
        variant: Visual style — "default", "secondary", or "outline".
    """
    return shinyreact.Node(
        type="shadcn:Badge",
        props={"text": text, "variant": variant},
    )


def button(
    input_id: str,
    label: str,
    *,
    variant: Literal["default", "outline", "secondary", "ghost"] = "default",
) -> shinyreact.Node:
    """An action button. Server reads ``input.<input_id>()`` as a click counter.

    Args:
        input_id: Shiny input id.
        label: Button label text.
        variant: Visual style — "default", "outline", "secondary", or "ghost".
    """
    return shinyreact.Node(
        type="shadcn:Button",
        props={"input_id": input_id, "label": label, "variant": variant},
    )


def calendar(
    input_id: str,
    *,
    selected: str | None = None,
) -> shinyreact.Node:
    """A single-date picker. Server reads ``input.<input_id>()`` as an ISO date string.

    The value crosses the wire as ``"YYYY-MM-DD"`` (or ``None``). Parse it with
    ``datetime.date.fromisoformat(input.<input_id>())``.

    Args:
        input_id: Shiny input id.
        selected: Initial date as an ISO string ``"YYYY-MM-DD"``.
    """
    return shinyreact.Node(
        type="shadcn:Calendar",
        props={"input_id": input_id, "selected": selected},
    )


def card(
    *children: object,
    title: str | None = None,
) -> shinyreact.Node:
    """A card container with an optional header title.

    Args:
        *children: Child nodes rendered inside the card body.
        title: Optional card header text.
    """
    return shinyreact.Node(
        type="shadcn:Card",
        props={"title": title} if title else {},
        children=list(children),
    )


def text_input(
    input_id: str,
    *,
    placeholder: str = "",
    label: str | None = None,
    debounce_ms: int = 250,
) -> shinyreact.Node:
    """A text input field. Server reads ``input.<input_id>()`` as the current string.

    Args:
        input_id: Shiny input id.
        placeholder: Placeholder text shown when the input is empty.
        label: Optional label displayed above the input.
        debounce_ms: Debounce delay in milliseconds before the value is sent.
    """
    return shinyreact.Node(
        type="shadcn:Input",
        props={
            "input_id": input_id,
            "placeholder": placeholder,
            "label": label,
            "debounce_ms": debounce_ms,
        },
    )


def separator(
    *,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
) -> shinyreact.Node:
    """A thin rule line for visual separation.

    Args:
        orientation: "horizontal" (full-width line) or "vertical" (full-height line).
    """
    return shinyreact.Node(
        type="shadcn:Separator",
        props={"orientation": orientation},
    )


def select(
    input_id: str,
    choices: list[Union[str, dict[str, str]]],
    *,
    selected: str | None = None,
    label: str | None = None,
) -> shinyreact.Node:
    """A dropdown select. Server reads ``input.<input_id>()`` as the selected string.

    Args:
        input_id: Shiny input id.
        choices: List of strings or ``{"value": ..., "label": ...}`` dicts.
        selected: Initially selected value (defaults to first choice).
        label: Optional label displayed above the select.
    """
    return shinyreact.Node(
        type="shadcn:Select",
        props={
            "input_id": input_id,
            "choices": choices,
            "selected": selected,
            "label": label,
        },
    )


def slider(
    input_id: str,
    *,
    min: int | float = 0,
    max: int | float = 100,
    step: int | float = 1,
    value: int | float = 50,
    label: str | None = None,
) -> shinyreact.Node:
    """A numeric range slider. Server reads ``input.<input_id>()`` as a number.

    Args:
        input_id: Shiny input id.
        min: Minimum value.
        max: Maximum value.
        step: Step increment.
        value: Initial value.
        label: Optional label displayed above the slider (current value shown right).
    """
    return shinyreact.Node(
        type="shadcn:Slider",
        props={
            "input_id": input_id,
            "min": min,
            "max": max,
            "step": step,
            "value": value,
            "label": label,
        },
    )


def switch(
    input_id: str,
    *,
    label: str | None = None,
    checked: bool = False,
) -> shinyreact.Node:
    """A toggle switch. Server reads ``input.<input_id>()`` as a boolean.

    Args:
        input_id: Shiny input id.
        label: Optional label shown beside the switch.
        checked: Initial checked state.
    """
    return shinyreact.Node(
        type="shadcn:Switch",
        props={
            "input_id": input_id,
            "label": label,
            "checked": checked,
        },
    )


def alert(
    description: str,
    *,
    title: str | None = None,
    variant: Literal["default", "destructive"] = "default",
) -> shinyreact.Node:
    """A status alert box. Display-only — no Shiny input.

    Args:
        description: Alert body text.
        title: Optional bold title shown above the description.
        variant: "default" (neutral) or "destructive" (red, for errors/warnings).
    """
    return shinyreact.Node(
        type="shadcn:Alert",
        props={
            "title": title,
            "description": description,
            "variant": variant,
        },
    )


def checkbox(
    input_id: str,
    label: str,
    *,
    checked: bool = False,
) -> shinyreact.Node:
    """A checkbox. Server reads ``input.<input_id>()`` as a boolean.

    Args:
        input_id: Shiny input id.
        label: Label text shown beside the checkbox.
        checked: Initial checked state.
    """
    return shinyreact.Node(
        type="shadcn:Checkbox",
        props={
            "input_id": input_id,
            "label": label,
            "checked": checked,
        },
    )


def dialog(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    title: str | None = None,
    description: str | None = None,
) -> shinyreact.Node:
    """A modal dialog. Server reads ``input.<input_id>()`` as bool (open state).

    Args:
        input_id: Shiny input id — ``True`` while the dialog is open.
        *children: Content nodes rendered inside the dialog body.
        trigger_label: Label on the button that opens the dialog.
        title: Optional dialog title.
        description: Optional muted subtitle shown below the title.
    """
    return shinyreact.Node(
        type="shadcn:Dialog",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "title": title,
            "description": description,
        },
        children=list(children),
    )


def popover(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    align: Literal["start", "center", "end"] = "center",
) -> shinyreact.Node:
    """A floating popover. Server reads ``input.<input_id>()`` as bool (open state).

    Args:
        input_id: Shiny input id — ``True`` while the popover is open.
        *children: Content nodes rendered inside the popover.
        trigger_label: Label on the button that opens the popover.
        align: Horizontal alignment of the panel relative to the trigger.
    """
    return shinyreact.Node(
        type="shadcn:Popover",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "align": align,
        },
        children=list(children),
    )


# --- Dropdown menu (data-driven compound component) -------------------------
# A menu is a structured list of actions, so its contents are passed as a data
# array (`items`), not as nested Nodes. Use the menu_* builders below to make
# each item — they return plain dicts that serialize straight to the JS bridge.


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
    """
    return shinyreact.Node(
        type="shadcn:DropdownMenu",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "items": list(items),
        },
    )


def table(
    columns: list[str],
    rows: list[list[object]],
    *,
    caption: str | None = None,
) -> shinyreact.Node:
    """A display-only data table. No Shiny input.

    Args:
        columns: Header labels.
        rows: Each row is a list of cell values (strings or numbers).
        caption: Optional caption shown below the table.
    """
    return shinyreact.Node(
        type="shadcn:Table",
        props={"columns": columns, "rows": rows, "caption": caption},
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
) -> shinyreact.Node:
    """A tabbed panel. ``tabs`` defines the triggers; ``panels`` are the content.

    Panels are matched to tabs positionally — the Nth panel renders under the
    Nth tab. Server reads ``input.<input_id>()`` as the active tab's value.

    Args:
        input_id: Shiny input id for the active tab (two-way).
        tabs: Tab trigger specs, built with :func:`tab`.
        *panels: One content node per tab, in the same order as ``tabs``.
        selected: Initially active tab value (defaults to the first tab).
    """
    return shinyreact.Node(
        type="shadcn:Tabs",
        props={"input_id": input_id, "tabs": tabs, "selected": selected},
        children=list(panels),
    )


# --- Toaster (server-push, message-handler pattern) -------------------------
# A toast host has no input and no trigger — the server PUSHES toasts to it.
# Mount `toaster()` once in the UI, then call `toast(session, ...)` from the
# server to display a notification.


def toaster(
    *,
    message_type: str = "toast",
    position: str = "bottom-right",
) -> shinyreact.Node:
    """A toast host. Mount once; the server pushes toasts to it via :func:`toast`.

    Args:
        message_type: The ``send_message`` type this host listens for. Must
            match the ``message_type`` passed to :func:`toast`.
        position: Corner to show toasts in, e.g. "bottom-right", "top-center".
    """
    return shinyreact.Node(
        type="shadcn:Toaster",
        props={"message_type": message_type, "position": position},
    )


async def toast(
    session: object,
    message: str,
    *,
    description: str | None = None,
    type: Literal[
        "default", "success", "info", "warning", "error", "loading"
    ] = "default",
    duration: int | None = None,
    message_type: str = "toast",
) -> None:
    """Push a toast to a :func:`toaster` host from the server.

    Args:
        session: The Shiny session.
        message: The toast's main text.
        description: Optional secondary line.
        type: Visual style / icon.
        duration: Milliseconds to show the toast (sonner default if omitted).
        message_type: Must match the host's ``message_type``.
    """
    await shinyreact.send_message(
        session,
        message_type,
        {
            "message": message,
            "description": description,
            "type": type,
            "duration": duration,
        },
    )
