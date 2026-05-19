"""Parent-tag context stack — backs shinyuiclassonly's ``with``-block child collection.

Verbatim port of ``shinyui._ctx_stack``. The mechanism is session-free —
just a ContextVar-backed parent stack plus a process-wide
``sys.displayhook`` shim that routes displayed values to the active
parent's ``append`` method via ``htmltools.wrap_displayhook_handler``.

See ``shinyui/_ctx_stack.py`` for the design notes; behavior is identical.
"""

from __future__ import annotations

import contextvars
import sys
from typing import Any, Callable

from htmltools import wrap_displayhook_handler

_stack: contextvars.ContextVar[tuple[Any, ...]] = contextvars.ContextVar(
    "shinyuiclassonly_parent_stack", default=()
)
_installed: bool = False
_prev_displayhook: Callable[[object], None] | None = None


def _dispatch(x: object) -> None:
    stack = _stack.get()
    if stack:
        wrap_displayhook_handler(stack[-1].append)(x)
    else:
        assert _prev_displayhook is not None
        _prev_displayhook(x)


def _ensure_installed() -> None:
    global _installed, _prev_displayhook
    if not _installed:
        _prev_displayhook = sys.displayhook
        sys.displayhook = _dispatch
        _installed = True


def push(parent: Any) -> contextvars.Token[tuple[Any, ...]]:
    """Push ``parent`` onto the current task's parent stack and return the
    reset Token. Lazily installs the global displayhook shim on first call.
    """
    _ensure_installed()
    return _stack.set(_stack.get() + (parent,))


def pop(token: contextvars.Token[tuple[Any, ...]]) -> None:
    """Restore the stack to its snapshot at the time ``token`` was issued."""
    _stack.reset(token)


def dispatch_to_active_parent(x: Any) -> None:
    """Forward ``x`` to the active parent — the next outer ``with``-block parent
    if one exists, otherwise the displayhook that was installed before ours.
    """
    sys.displayhook(x)
