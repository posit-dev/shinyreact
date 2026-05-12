"""Python factory functions for MUI components.

Each factory returns a ``shinyreact.Node`` with a ``mui:``-namespaced type
string. Components are added one per task.
"""

from typing import Literal

import shinyreact


def button(
    label: str,
    *,
    input_id: str,
    variant: Literal["text", "contained", "outlined"] = "contained",
    color: Literal["primary", "secondary", "success", "error"] = "primary",
    start_icon: str | None = None,
    end_icon: str | None = None,
) -> shinyreact.Node:
    """Render an MUI Button.

    ``input_id`` is required — clicks increment an action-button counter sent
    to ``input.<input_id>()``, following the shinyreact action-button pattern.

    ``start_icon`` and ``end_icon`` are MUI icon names (e.g. ``"Save"``,
    ``"Send"``); the JS component looks them up in ``@mui/icons-material``.
    """
    props: dict[str, object] = {
        "label": label,
        "input_id": input_id,
        "variant": variant,
        "color": color,
    }
    if start_icon is not None:
        props["start_icon"] = start_icon
    if end_icon is not None:
        props["end_icon"] = end_icon
    return shinyreact.Node(type="mui:Button", props=props)


def text_field(
    *,
    input_id: str,
    label: str = "",
    default_value: str = "",
    placeholder: str = "",
    helper_text: str = "",
    debounce_ms: int = 250,
) -> shinyreact.Node:
    """Render an MUI TextField bound to a Shiny input."""
    return shinyreact.Node(
        type="mui:TextField",
        props={
            "input_id": input_id,
            "label": label,
            "default_value": default_value,
            "placeholder": placeholder,
            "helper_text": helper_text,
            "debounce_ms": debounce_ms,
        },
    )


def slider(
    *,
    input_id: str,
    label: str = "",
    default_value: float = 0,
    min: float = 0,
    max: float = 100,
    step: float = 1,
    debounce_ms: int = 100,
) -> shinyreact.Node:
    """Render an MUI Slider bound to a Shiny input."""
    return shinyreact.Node(
        type="mui:Slider",
        props={
            "input_id": input_id,
            "label": label,
            "default_value": default_value,
            "min": min,
            "max": max,
            "step": step,
            "debounce_ms": debounce_ms,
        },
    )


def card(
    title: str | None = None,
    *children: shinyreact.Node,
) -> shinyreact.Node:
    """Render an MUI Card. Children become the card body."""
    props: dict[str, object] = {}
    if title is not None:
        props["title"] = title
    return shinyreact.Node(type="mui:Card", props=props, children=list(children))
