"""Tests for shinyui's parent-tag context stack (issue #70, Stage A).

Direct push/pop and displayhook tests live here; the AllowsChildren
integration tests live in test_allows_children.py.
"""

from __future__ import annotations

import sys

import shinyui as sui
from htmltools import tags


def test_push_pop_isolated_stack() -> None:
    """push/pop maintain a stack via Token-based reset."""
    from shinyui._ctx_stack import _stack, pop, push

    assert _stack.get() == ()
    parent_a = sui.card(id="a")
    token_a = push(parent_a)
    assert _stack.get() == (parent_a,)
    parent_b = sui.card(id="b")
    token_b = push(parent_b)
    assert _stack.get() == (parent_a, parent_b)
    pop(token_b)
    assert _stack.get() == (parent_a,)
    pop(token_a)
    assert _stack.get() == ()


def test_displayhook_routes_to_stack_tip_via_push() -> None:
    """sys.displayhook(value) while a parent is on the stack appends to it."""
    from shinyui._ctx_stack import pop, push

    c = sui.card(id="m")
    token = push(c)
    try:
        sys.displayhook(tags.p("hi"))
    finally:
        pop(token)
    assert len(c.children) == 1


def test_displayhook_fall_through_outside_with_block() -> None:
    """sys.displayhook(value) with empty stack delegates to prior displayhook."""
    from shinyui._ctx_stack import _ensure_installed

    _ensure_installed()

    seen: list[object] = []
    import shinyui._ctx_stack as cs

    original_prev = cs._prev_displayhook
    cs._prev_displayhook = seen.append
    try:
        sys.displayhook("untargeted")
    finally:
        cs._prev_displayhook = original_prev

    assert seen == ["untargeted"]
