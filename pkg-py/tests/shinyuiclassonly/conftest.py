"""Shared fixtures for shinyuiclassonly tests.

No session fixtures here — shinyuiclassonly is session-free.
"""

from __future__ import annotations

from typing import Iterator

import pytest


@pytest.fixture(autouse=True)
def _reset_ctx_stack() -> Iterator[None]:
    """Isolate the parent-tag context stack between tests.

    The stack lives in a process-wide ContextVar. In a sync pytest run,
    tests share the same context, so a test that forgets to pop a parent
    would dirty every subsequent test. Reset on both edges.
    """
    from shinyuiclassonly._ctx_stack import _stack

    token = _stack.set(())
    try:
        yield
    finally:
        _stack.reset(token)
