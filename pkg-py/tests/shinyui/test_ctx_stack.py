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
    try:
        assert _stack.get() == (parent_a,)
        parent_b = sui.card(id="b")
        token_b = push(parent_b)
        try:
            assert _stack.get() == (parent_a, parent_b)
        finally:
            pop(token_b)
        assert _stack.get() == (parent_a,)
    finally:
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
    assert c.children[0].name == "p"


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


def test_ctx_tag_as_context_manager_collects_children() -> None:
    """CtxTag.__enter__ pushes onto the stack so bare expressions collect."""
    outer = sui.CtxTag("div")
    with outer as d:
        sys.displayhook(sui.CtxTag("h1", "Title"))
        sys.displayhook("body text")
    assert len(d.children) == 2
    assert d.children[0].name == "h1"
    assert d.children[1] == "body text"


def test_ctx_tag_outside_with_block_behaves_like_tag() -> None:
    """Constructing a CtxTag outside any with-block does not touch the stack."""
    t = sui.CtxTag("span", "ok")
    assert t.name == "span"
    assert "ok" in list(t.children)


def test_ctx_tag_overrides_htmltools_displayhook_swap() -> None:
    """CtxTag.__enter__ must NOT do htmltools' global sys.displayhook swap.

    htmltools.Tag.__enter__ sets self.prev_displayhook; if our subclass
    delegates to super().__enter__, that side-effect would happen. Verify
    it does not."""
    t = sui.CtxTag("div")
    with t:
        pass
    assert t.prev_displayhook is None
