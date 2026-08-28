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

from ._dep_discovery import install_dep_discovery

if TYPE_CHECKING:
    from shiny.module import ResolvedId
    from shiny.session import Session


# force=True so re-importing this module (e.g. importlib.reload during dev or
# tests) re-registers idempotently instead of raising "already registered".
@input_handlers.add("shinyreact.default", force=True)
def _shinyreact_default(value: Any, name: ResolvedId, session: Session) -> Any:
    return value


@input_handlers.add("shinyreact.asis", force=True)
def _shinyreact_asis(value: Any, name: ResolvedId, session: Session) -> Any:
    return value


# The JS bundle sends one `.shinyreact_init:shinyreact.init` ping per session
# after Shiny initializes (pkg-js/src/dep-discovery.ts); the handler bootstraps
# automatic output dependency discovery, matching R (issue #220).
@input_handlers.add("shinyreact.init", force=True)
def _shinyreact_init(value: Any, name: ResolvedId, session: Session) -> Any:
    install_dep_discovery(session)
    return value
