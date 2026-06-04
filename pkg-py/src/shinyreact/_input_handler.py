"""Built-in shinyreact input handlers, registered on import.

See docs/superpowers/specs/2026-06-04-shinyreact-default-input-handler-design.md.

Python's deserializer never simplifies the way R's does (an array of objects is
already a list of dicts), so both handlers are no-ops here. They exist so that
the ``:shinyreact.default`` / ``:shinyreact.asis`` wire suffixes do not raise
"No input handler registered for type" on the Python server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shiny.input_handler import input_handlers

if TYPE_CHECKING:
    from shiny.module import ResolvedId
    from shiny.session import Session


@input_handlers.add("shinyreact.default", force=True)
def _shinyreact_default(value: Any, name: ResolvedId, session: Session) -> Any:
    return value


@input_handlers.add("shinyreact.asis", force=True)
def _shinyreact_asis(value: Any, name: ResolvedId, session: Session) -> Any:
    return value
