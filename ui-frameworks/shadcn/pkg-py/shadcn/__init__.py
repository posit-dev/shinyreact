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
