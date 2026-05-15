"""Parent-tag context stack — backs shinyui's ``with``-block child collection.

The mechanism:

1. A module-level ``contextvars.ContextVar`` holds an immutable tuple stack of
   "active parents." Per-task isolation comes from ``ContextVar`` semantics —
   each ``asyncio.Task`` gets its own copy on creation.
2. The first time any parent is entered, we lazily install a process-wide
   ``sys.displayhook`` shim. The shim reads the current task's stack:
   - non-empty → append the displayed value to the stack tip via
     ``htmltools.wrap_displayhook_handler`` (which knows how to coerce
     strings, Tags, TagLists, Tagifiables, ReprHtml, etc.).
   - empty → delegate to the displayhook that was installed *before* ours
     (preserves REPL/Jupyter behavior, anything else built on displayhook).
3. ``__enter__`` calls ``push(self)`` to capture a ``Token``; ``__exit__``
   calls ``pop(token)`` to restore the prior stack snapshot. The Token-based
   reset is robust to exceptions in the ``with`` body.

This module is private. ``AllowsChildren`` (in ``_children.py``) and
``CtxTag`` (in ``_ctx_tag.py``) call ``push``/``pop`` to track scope.
``AllowsChildren.__exit__`` additionally calls ``dispatch_to_active_parent``
to propagate the just-closed component. When an outer parent is still on
the stack, the component is appended there; when the stack is empty
(outermost ``with``), it falls through via ``sys.displayhook`` so
REPL/Jupyter/Express can place it. This mirrors ``htmltools.Tag.__exit__``'s
behavior of forwarding self to the outer scope.
"""

from __future__ import annotations

import contextvars
import sys
from typing import Any, Callable

from htmltools import wrap_displayhook_handler

_stack: contextvars.ContextVar[tuple[Any, ...]] = contextvars.ContextVar(
    "shinyui_parent_stack", default=()
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

    Called by ``AllowsChildren.__exit__`` so nested ``with`` blocks propagate
    the just-closed component to the enclosing parent. When the outermost
    ``with`` exits, the stack is empty — falling through to ``_prev_displayhook``
    lets Express (or REPL/Jupyter) place the top-level component as if it had
    been a bare expression statement.
    """
    sys.displayhook(x)
