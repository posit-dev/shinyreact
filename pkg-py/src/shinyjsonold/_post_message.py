from __future__ import annotations

from typing import TYPE_CHECKING

from shiny.module import resolve_id

if TYPE_CHECKING:
    from shiny.session import Session
    from shiny.types import Jsonifiable


async def post_message(
    session: Session,
    type: str,
    data: Jsonifiable,
) -> None:
    """Send a custom message from server to client React components.

    Messages are consumed by ``useShinyMessageHandler(type, handler)``
    on the React side via the ``@posit/shiny-react`` hooks bundled in shinyjson.

    Args:
        session: The Shiny session to send the message through.
        type: The message type string. Must match the ``messageType`` argument
            passed to ``useShinyMessageHandler()`` in the React component.
        data: Any JSON-serializable data to include in the message.

    Example::

        @reactive.effect
        async def send_notification():
            await shinyjson.post_message(
                session, "notification", {"text": "Hello!", "level": "info"}
            )
    """
    namespaced_type = resolve_id(type)
    await session.send_custom_message(
        "shinyReactMessage", {"type": namespaced_type, "data": data}
    )
