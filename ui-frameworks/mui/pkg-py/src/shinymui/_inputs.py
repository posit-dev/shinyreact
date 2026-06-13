from __future__ import annotations

from typing import Literal

import shinyreact


def autocomplete(
    input_id: str,
    options: list[str],
    *,
    label: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """An autocomplete combobox. Server reads ``input.<input_id>()`` as the
    selected option.

    Args:
        input_id: Shiny input id.
        options: List of option strings.
        label: Floating label text on the input.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Autocomplete",
        props={
            "input_id": input_id,
            "options": options,
            "label": label,
            "className": class_,
        },
    )


def bottom_navigation(
    input_id: str,
    items: list[dict[str, str]],
    *,
    class_: str | None = None,
) -> shinyreact.Node:
    """A bottom navigation bar. Server reads ``input.<input_id>()`` as the
    selected item value.

    Args:
        input_id: Shiny input id.
        items: List of ``{"value", "label"}`` dicts, one per action.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:BottomNavigation",
        props={"input_id": input_id, "items": items, "className": class_},
    )


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


def fab(
    input_id: str,
    label: str | None = None,
    *,
    color: Literal[
        "primary", "secondary", "success", "error", "info", "warning"
    ] = "primary",
    variant: Literal["circular", "extended"] = "circular",
    class_: str | None = None,
) -> shinyreact.Node:
    """A floating action button. Server reads ``input.<input_id>()`` as a click
    counter.

    Args:
        input_id: Shiny input id.
        label: Button content (icon or text).
        color: MUI theme color.
        variant: "circular" or "extended".
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Fab",
        props={
            "input_id": input_id,
            "label": label,
            "color": color,
            "variant": variant,
            "className": class_,
        },
    )


def pagination(
    input_id: str,
    *,
    count: int = 10,
    class_: str | None = None,
) -> shinyreact.Node:
    """A pagination bar. Server reads ``input.<input_id>()`` as the current page
    number (1-based).

    Args:
        input_id: Shiny input id.
        count: Total number of pages.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Pagination",
        props={"input_id": input_id, "count": count, "className": class_},
    )


def radio_group(
    input_id: str,
    choices: list[str] | list[dict[str, str]],
    *,
    label: str | None = None,
    selected: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A single-select radio group. Server reads ``input.<input_id>()`` as the
    selected value.

    Args:
        input_id: Shiny input id.
        choices: A list of value strings, or ``{"value", "label"}`` dicts.
        label: Optional label displayed above the group.
        selected: Initially selected value (defaults to first choice).
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:RadioGroup",
        props={
            "input_id": input_id,
            "choices": choices,
            "label": label,
            "selected": selected,
            "className": class_,
        },
    )


def rating(
    input_id: str,
    *,
    max: int = 5,
    precision: float = 1,
    class_: str | None = None,
) -> shinyreact.Node:
    """A star rating. Server reads ``input.<input_id>()`` as the current rating
    number.

    Args:
        input_id: Shiny input id.
        max: Maximum number of stars.
        precision: Smallest increment a star can be selected at.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Rating",
        props={
            "input_id": input_id,
            "max": max,
            "precision": precision,
            "className": class_,
        },
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


def tabs(
    input_id: str,
    tabs: list[dict[str, str]],
    *children: object,
    selected: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A tab bar with panels. Server reads ``input.<input_id>()`` as the selected
    tab value. The metadata in ``tabs`` drives the bar; positional children are
    the panels (one per tab, by position).

    Args:
        input_id: Shiny input id.
        tabs: List of ``{"value", "label"}`` dicts, one per tab.
        *children: Panel content nodes — one per tab, matched by position.
        selected: Initially selected tab value (defaults to first tab).
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Tabs",
        props={
            "input_id": input_id,
            "tabs": tabs,
            "selected": selected,
            "className": class_,
        },
        children=list(children),
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


def toggle_button_group(
    input_id: str,
    choices: list[str] | list[dict[str, str]],
    *,
    exclusive: bool = True,
    class_: str | None = None,
) -> shinyreact.Node:
    """A group of toggle buttons. Server reads ``input.<input_id>()`` as the
    selected value(s) — a string when ``exclusive`` is True, else a list.

    Args:
        input_id: Shiny input id.
        choices: A list of value strings, or ``{"value", "label"}`` dicts.
        exclusive: Allow only one active button when True.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:ToggleButtonGroup",
        props={
            "input_id": input_id,
            "choices": choices,
            "exclusive": exclusive,
            "className": class_,
        },
    )
