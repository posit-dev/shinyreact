"""Per-session map: input id -> HasInputValue instance.

Attached as `session._shinyui_instances` on first registration. This is a private
attribute on Shiny's Session — acceptable for a prototype; Stage B can negotiate
a public hook in py-shiny.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shiny.session import Session

    from ._input_value import HasInputValue

_ATTR = "_shinyui_instances"


def get_session_instances(session: "Session") -> dict[str, "HasInputValue"]:
    m = getattr(session, _ATTR, None)
    if m is None:
        m = {}
        setattr(session, _ATTR, m)
    return m


def register_instance(session: "Session", id: str, instance: "HasInputValue") -> None:
    get_session_instances(session)[id] = instance


def lookup_instance(session: "Session", id: str) -> "HasInputValue | None":
    return get_session_instances(session).get(id)
