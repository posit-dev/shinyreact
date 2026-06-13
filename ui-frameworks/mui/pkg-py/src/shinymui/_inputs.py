from __future__ import annotations

from typing import Literal

import shinyreact


def button(
    input_id: str,
    label: str = "Button",
    *,
    variant: Literal["contained", "outlined", "text"] = "contained",
    color: Literal[
        "primary", "secondary", "success", "error", "info", "warning"
    ] = "primary",
    class_: str | None = None,
) -> shinyreact.Node:
    """An action button. Server reads ``input.<input_id>()`` as a click counter.

    Args:
        input_id: Shiny input id.
        label: Button text.
        variant: MUI button variant.
        color: MUI theme color.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Button",
        props={
            "input_id": input_id,
            "label": label,
            "variant": variant,
            "color": color,
            "className": class_,
        },
    )


def text_field(
    input_id: str,
    *,
    label: str | None = None,
    placeholder: str | None = None,
    variant: Literal["outlined", "filled", "standard"] = "outlined",
    debounce_ms: int = 250,
    class_: str | None = None,
) -> shinyreact.Node:
    """A text field. Server reads ``input.<input_id>()`` as the current string.

    Args:
        input_id: Shiny input id.
        label: Floating label text.
        placeholder: Placeholder text.
        variant: MUI text-field variant.
        debounce_ms: Debounce before sending keystrokes to the server.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:TextField",
        props={
            "input_id": input_id,
            "label": label,
            "placeholder": placeholder,
            "variant": variant,
            "debounce_ms": debounce_ms,
            "className": class_,
        },
    )


def slider(
    input_id: str,
    *,
    min: float = 0,
    max: float = 100,
    step: float = 1,
    value: float = 50,
    class_: str | None = None,
) -> shinyreact.Node:
    """A slider. Server reads ``input.<input_id>()`` as a number.

    Args:
        input_id: Shiny input id.
        min: Minimum value.
        max: Maximum value.
        step: Step increment.
        value: Initial value.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Slider",
        props={
            "input_id": input_id,
            "min": min,
            "max": max,
            "step": step,
            "value": value,
            "className": class_,
        },
    )


def switch(
    input_id: str,
    *,
    label: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A toggle switch. Server reads ``input.<input_id>()`` as a boolean.

    Args:
        input_id: Shiny input id.
        label: Optional label beside the switch.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Switch",
        props={"input_id": input_id, "label": label, "className": class_},
    )


def checkbox(
    input_id: str,
    *,
    label: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A checkbox. Server reads ``input.<input_id>()`` as a boolean.

    Args:
        input_id: Shiny input id.
        label: Optional label beside the checkbox.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Checkbox",
        props={"input_id": input_id, "label": label, "className": class_},
    )


def select(
    input_id: str,
    choices: list[str] | list[dict[str, str]],
    *,
    label: str | None = None,
    selected: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A dropdown select. Server reads ``input.<input_id>()`` as the selected value.

    Args:
        input_id: Shiny input id.
        choices: A list of value strings, or ``{"value", "label"}`` dicts.
        label: Floating label text.
        selected: Initially selected value.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Select",
        props={
            "input_id": input_id,
            "choices": choices,
            "label": label,
            "selected": selected,
            "className": class_,
        },
    )
