from __future__ import annotations

from typing import Literal

import shinyreact


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
