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
