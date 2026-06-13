from __future__ import annotations

from typing import Literal

import shinyreact


def alert(
    text: str,
    *,
    severity: Literal["error", "warning", "info", "success"] = "info",
    variant: Literal["standard", "filled", "outlined"] = "standard",
    class_: str | None = None,
) -> shinyreact.Node:
    """A status message.

    Args:
        text: Message text.
        severity: Alert severity (controls color/icon).
        variant: MUI alert variant.
        class_: Extra CSS classes on the root element.
    """
    return shinyreact.Node(
        type="mui:Alert",
        props={
            "text": text,
            "severity": severity,
            "variant": variant,
            "className": class_,
        },
    )
