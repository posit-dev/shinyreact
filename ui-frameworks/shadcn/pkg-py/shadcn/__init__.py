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


_Variant = Literal["default", "secondary", "destructive", "outline", "ghost", "link"]
BadgeVariant = _Variant
ButtonVariant = _Variant
ButtonSize = Literal["default", "sm", "lg", "icon"]


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


def button(
    input_id: str,
    label: str,
    *,
    variant: ButtonVariant = "default",
    size: ButtonSize = "default",
    class_: str | None = None,
) -> shinyreact.Node:
    """An action button. Server reads ``input.<input_id>()`` as a click counter.

    Args:
        input_id: Shiny input id.
        label: Button label text.
        variant: Visual style — default, secondary, destructive, outline, ghost, link.
        size: "default", "sm", "lg", or "icon".
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Button",
        props={
            "input_id": input_id,
            "label": label,
            "variant": variant,
            "size": size,
            "className": class_,
        },
    )


def calendar(
    input_id: str,
    *,
    selected: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A single-date picker. Server reads ``input.<input_id>()`` as an ISO date string.

    The value crosses the wire as ``"YYYY-MM-DD"`` (or ``None``). Parse it with
    ``datetime.date.fromisoformat(input.<input_id>())``.

    Args:
        input_id: Shiny input id.
        selected: Initial date as an ISO string ``"YYYY-MM-DD"``.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Calendar",
        props={"input_id": input_id, "selected": selected, "className": class_},
    )


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


def text_input(
    input_id: str,
    *,
    placeholder: str = "",
    label: str | None = None,
    debounce_ms: int = 250,
    class_: str | None = None,
) -> shinyreact.Node:
    """A text input field. Server reads ``input.<input_id>()`` as the current string.

    Args:
        input_id: Shiny input id.
        placeholder: Placeholder text shown when the input is empty.
        label: Optional label displayed above the input.
        debounce_ms: Debounce delay in milliseconds before the value is sent.
        class_: Extra CSS classes merged onto the wrapper element.
    """
    return shinyreact.Node(
        type="shadcn:Input",
        props={
            "input_id": input_id,
            "placeholder": placeholder,
            "label": label,
            "debounce_ms": debounce_ms,
            "className": class_,
        },
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


def select(
    input_id: str,
    choices: list[Union[str, dict[str, str]]],
    *,
    selected: str | None = None,
    label: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A dropdown select. Server reads ``input.<input_id>()`` as the selected string.

    Args:
        input_id: Shiny input id.
        choices: List of strings or ``{"value": ..., "label": ...}`` dicts.
        selected: Initially selected value (defaults to first choice).
        label: Optional label displayed above the select.
        class_: Extra CSS classes merged onto the wrapper element.
    """
    return shinyreact.Node(
        type="shadcn:Select",
        props={
            "input_id": input_id,
            "choices": choices,
            "selected": selected,
            "label": label,
            "className": class_,
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
    class_: str | None = None,
) -> shinyreact.Node:
    """A numeric range slider. Server reads ``input.<input_id>()`` as a number.

    Args:
        input_id: Shiny input id.
        min: Minimum value.
        max: Maximum value.
        step: Step increment.
        value: Initial value.
        label: Optional label displayed above the slider (current value shown right).
        class_: Extra CSS classes merged onto the wrapper element.
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
            "className": class_,
        },
    )


def switch(
    input_id: str,
    *,
    label: str | None = None,
    checked: bool = False,
    class_: str | None = None,
) -> shinyreact.Node:
    """A toggle switch. Server reads ``input.<input_id>()`` as a boolean.

    Args:
        input_id: Shiny input id.
        label: Optional label shown beside the switch.
        checked: Initial checked state.
        class_: Extra CSS classes merged onto the wrapper element.
    """
    return shinyreact.Node(
        type="shadcn:Switch",
        props={
            "input_id": input_id,
            "label": label,
            "checked": checked,
            "className": class_,
        },
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


def checkbox(
    input_id: str,
    label: str,
    *,
    checked: bool = False,
    class_: str | None = None,
) -> shinyreact.Node:
    """A checkbox. Server reads ``input.<input_id>()`` as a boolean.

    Args:
        input_id: Shiny input id.
        label: Label text shown beside the checkbox.
        checked: Initial checked state.
        class_: Extra CSS classes merged onto the wrapper element.
    """
    return shinyreact.Node(
        type="shadcn:Checkbox",
        props={
            "input_id": input_id,
            "label": label,
            "checked": checked,
            "className": class_,
        },
    )


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


# --- Toaster (server-push, message-handler pattern) -------------------------
# A toast host has no input and no trigger — the server PUSHES toasts to it.
# Mount `toaster()` once in the UI, then call `toast(session, ...)` from the
# server to display a notification.


def toaster(
    *,
    message_type: str = "toast",
    position: str = "bottom-right",
    class_: str | None = None,
) -> shinyreact.Node:
    """A toast host. Mount once; the server pushes toasts to it via :func:`toast`.

    Args:
        message_type: The ``send_message`` type this host listens for. Must
            match the ``message_type`` passed to :func:`toast`.
        position: Corner to show toasts in, e.g. "bottom-right", "top-center".
        class_: Extra CSS classes merged onto the toaster element.
    """
    return shinyreact.Node(
        type="shadcn:Toaster",
        props={
            "message_type": message_type,
            "position": position,
            "className": class_,
        },
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


def textarea(
    input_id: str,
    *,
    placeholder: str = "",
    label: str | None = None,
    debounce_ms: int = 250,
    class_: str | None = None,
) -> shinyreact.Node:
    """A multi-line text input. Server reads ``input.<input_id>()`` as a string.

    Args:
        input_id: Shiny input id.
        placeholder: Placeholder text shown when empty.
        label: Optional label displayed above the textarea.
        debounce_ms: Debounce delay in milliseconds before the value is sent.
        class_: Extra CSS classes merged onto the wrapper element.
    """
    return shinyreact.Node(
        type="shadcn:Textarea",
        props={
            "input_id": input_id,
            "placeholder": placeholder,
            "label": label,
            "debounce_ms": debounce_ms,
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


def toggle(
    input_id: str,
    label: str,
    *,
    pressed: bool = False,
    variant: Literal["default", "outline"] = "default",
    size: Literal["default", "sm", "lg"] = "default",
    class_: str | None = None,
) -> shinyreact.Node:
    """A two-state toggle button. Server reads ``input.<input_id>()`` as a boolean.

    Args:
        input_id: Shiny input id.
        label: Text/aria-label shown on the toggle.
        pressed: Initial pressed state.
        variant: "default" or "outline".
        size: "default", "sm", or "lg".
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Toggle",
        props={
            "input_id": input_id,
            "label": label,
            "pressed": pressed,
            "variant": variant,
            "size": size,
            "className": class_,
        },
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


def toggle_group(
    input_id: str,
    choices: list[Union[str, dict[str, str]]],
    *,
    type: Literal["single", "multiple"] = "single",
    selected: object | None = None,
    variant: Literal["default", "outline"] = "outline",
    size: Literal["default", "sm", "lg"] = "default",
    class_: str | None = None,
) -> shinyreact.Node:
    """A group of toggle buttons. Server reads ``input.<input_id>()`` as the
    selected value (string for "single", list for "multiple").

    Args:
        input_id: Shiny input id.
        choices: List of strings or ``{"value": ..., "label": ...}`` dicts.
        type: "single" (one active) or "multiple" (many).
        selected: Initial value (str or list).
        variant: "default" or "outline".
        size: "default", "sm", or "lg".
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:ToggleGroup",
        props={
            "input_id": input_id,
            "choices": choices,
            "type": type,
            "selected": selected,
            "variant": variant,
            "size": size,
            "className": class_,
        },
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


def carousel(
    *children: object,
    input_id: str | None = None,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    loop: bool = False,
    class_: str | None = None,
) -> shinyreact.Node:
    """A slide carousel. Children = the slide content (one child per slide).

    Args:
        *children: Content nodes — each becomes one slide.
        input_id: Optional Shiny input id; set to 0-based current slide index.
        orientation: "horizontal" or "vertical".
        loop: Whether the carousel loops around at the ends.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Carousel",
        props={
            "input_id": input_id,
            "orientation": orientation,
            "loop": loop,
            "className": class_,
        },
        children=list(children),
    )


def input_otp(
    input_id: str,
    *,
    length: int = 6,
    separator: bool = False,
    class_: str | None = None,
) -> shinyreact.Node:
    """A one-time password input. Server reads ``input.<input_id>()`` as a string.

    Args:
        input_id: Shiny input id.
        length: Number of OTP slots.
        separator: Show a dash separator between the two halves.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:InputOtp",
        props={
            "input_id": input_id,
            "length": length,
            "separator": separator,
            "className": class_,
        },
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


def command(
    input_id: str,
    items: list[dict[str, object]],
    *,
    placeholder: str = "Search...",
    empty_label: str = "No results found.",
    class_: str | None = None,
) -> shinyreact.Node:
    """A command palette / filterable list. Server reads ``input.<input_id>()`` as
    the selected item's value string.

    Args:
        input_id: Shiny input id.
        items: List of ``{"value": ..., "label": ..., "group": ...}`` dicts.
            ``group`` is optional — items with the same group appear under one heading.
        placeholder: Search input placeholder text.
        empty_label: Text shown when no items match the search.
        class_: Extra CSS classes merged onto the root element.
    """
    return shinyreact.Node(
        type="shadcn:Command",
        props={
            "input_id": input_id,
            "items": items,
            "placeholder": placeholder,
            "empty_label": empty_label,
            "className": class_,
        },
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


def radio_group(
    input_id: str,
    choices: list[Union[str, dict[str, str]]],
    *,
    selected: str | None = None,
    label: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A single-select radio group. Server reads ``input.<input_id>()`` as a string.

    Args:
        input_id: Shiny input id.
        choices: List of strings or ``{"value": ..., "label": ...}`` dicts.
        selected: Initially selected value (defaults to first choice).
        label: Optional label displayed above the group.
        class_: Extra CSS classes merged onto the wrapper element.
    """
    return shinyreact.Node(
        type="shadcn:RadioGroup",
        props={
            "input_id": input_id,
            "choices": choices,
            "selected": selected,
            "label": label,
            "className": class_,
        },
    )
