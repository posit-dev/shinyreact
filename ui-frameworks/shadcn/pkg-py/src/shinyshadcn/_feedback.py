from __future__ import annotations

import shinyreact


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
