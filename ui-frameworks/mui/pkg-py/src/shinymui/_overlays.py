from __future__ import annotations

import shinyreact


def dialog(
    input_id: str,
    *children: object,
    trigger_label: str = "Open",
    title: str | None = None,
    class_: str | None = None,
) -> shinyreact.Node:
    """A modal dialog. Server reads ``input.<input_id>()`` as the boolean open state.

    Args:
        input_id: Shiny input id tracking the open state.
        *children: Child nodes rendered in the dialog body.
        trigger_label: Text on the button that opens the dialog.
        title: Optional dialog title.
        class_: Extra CSS classes on the dialog root.
    """
    return shinyreact.Node(
        type="mui:Dialog",
        props={
            "input_id": input_id,
            "trigger_label": trigger_label,
            "title": title,
            "className": class_,
        },
        children=list(children),
    )
