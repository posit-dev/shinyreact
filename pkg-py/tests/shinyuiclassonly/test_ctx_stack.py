"""Tests for shinyuiclassonly's parent-tag context stack and CtxTag.

Verbatim parallel of pkg-py/tests/shinyui/test_ctx_stack.py, scoped to
the components shinyuiclassonly actually ships (no input_slider used
inside the expressify round-trip, since that comes later — keep this
test independent of component-class details).
"""

from __future__ import annotations

import asyncio
import sys

import pytest
import shinyuiclassonly as sui
from htmltools import tags


def test_push_pop_isolated_stack() -> None:
    from shinyuiclassonly._ctx_stack import _stack, pop, push

    assert _stack.get() == ()
    parent_a = sui.CtxTag("div", id="a")
    token_a = push(parent_a)
    try:
        assert _stack.get() == (parent_a,)
        parent_b = sui.CtxTag("div", id="b")
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
    from shinyuiclassonly._ctx_stack import pop, push

    c = sui.CtxTag("div")
    token = push(c)
    try:
        sys.displayhook(tags.p("hi"))
    finally:
        pop(token)
    assert len(c.children) == 1
    assert c.children[0].name == "p"


def test_displayhook_fall_through_outside_with_block() -> None:
    from shinyuiclassonly._ctx_stack import _ensure_installed

    _ensure_installed()

    seen: list[object] = []
    import shinyuiclassonly._ctx_stack as cs

    original_prev = cs._prev_displayhook
    cs._prev_displayhook = seen.append
    try:
        sys.displayhook("untargeted")
    finally:
        cs._prev_displayhook = original_prev

    assert seen == ["untargeted"]


def test_ctx_tag_as_context_manager_collects_children() -> None:
    outer = sui.CtxTag("div")
    with outer as d:
        sys.displayhook(sui.CtxTag("h1", "Title"))
        sys.displayhook("body text")
    assert len(d.children) == 2
    assert d.children[0].name == "h1"
    assert d.children[1] == "body text"


def test_ctx_tag_outside_with_block_behaves_like_tag() -> None:
    t = sui.CtxTag("span", "ok")
    assert t.name == "span"
    assert "ok" in list(t.children)


def test_ctx_tag_overrides_htmltools_displayhook_swap() -> None:
    t = sui.CtxTag("div")
    with t:
        pass
    assert t.prev_displayhook is None


@pytest.mark.asyncio
async def test_concurrent_tasks_have_isolated_stacks() -> None:
    started_a = asyncio.Event()
    started_b = asyncio.Event()
    finish = asyncio.Event()

    a_div: sui.CtxTag | None = None
    b_div: sui.CtxTag | None = None

    async def task_a() -> None:
        nonlocal a_div
        with sui.CtxTag("div", id="A") as da:
            a_div = da
            sys.displayhook(tags.p("a1"))
            started_a.set()
            await started_b.wait()
            sys.displayhook(tags.p("a2"))
            await finish.wait()
            sys.displayhook(tags.p("a3"))

    async def task_b() -> None:
        nonlocal b_div
        await started_a.wait()
        with sui.CtxTag("div", id="B") as db:
            b_div = db
            sys.displayhook(tags.p("b1"))
            started_b.set()
            await asyncio.sleep(0)
            sys.displayhook(tags.p("b2"))

    a = asyncio.create_task(task_a())
    b = asyncio.create_task(task_b())
    await b
    finish.set()
    await a

    assert a_div is not None and b_div is not None
    a_p = [c for c in a_div.children if hasattr(c, "name") and c.name == "p"]
    b_p = [c for c in b_div.children if hasattr(c, "name") and c.name == "p"]
    assert len(a_p) == 3
    assert len(b_p) == 2
