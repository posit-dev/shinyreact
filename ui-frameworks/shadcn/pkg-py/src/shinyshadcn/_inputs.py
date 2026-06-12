from __future__ import annotations

from typing import Literal, Union

import shinyreact

from ._types import ButtonSize, ButtonVariant


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


def pagination(
    input_id: str,
    *,
    total_pages: int = 10,
    current: int = 1,
    show_ellipsis: bool = True,
    class_: str | None = None,
) -> shinyreact.Node:
    """A page-number pagination bar.

    Server reads ``input.<input_id>()`` as int (1-based).

    Args:
        input_id: Shiny input id — current page number (1-based).
        total_pages: Total number of pages.
        current: Initially selected page (default 1).
        show_ellipsis: Collapse distant pages into ellipsis when True.
        class_: Extra CSS classes merged onto the nav element.
    """
    return shinyreact.Node(
        type="shadcn:Pagination",
        props={
            "input_id": input_id,
            "total_pages": total_pages,
            "current": current,
            "show_ellipsis": show_ellipsis,
            "className": class_,
        },
    )
