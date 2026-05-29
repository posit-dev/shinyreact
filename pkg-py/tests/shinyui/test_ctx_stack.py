"""Tests for shinyui's parent-tag context stack (issue #70, Stage A).

Direct push/pop and displayhook tests live here; the AllowsChildren
integration tests live in test_allows_children.py.
"""

from __future__ import annotations

import asyncio
import re
import sys

import pytest
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


def test_ensure_installed_reinstalls_when_displayhook_swapped() -> None:
    """If something else swaps ``sys.displayhook`` between push calls — e.g.
    Shiny Express's ``RecallContextManager`` entering and replacing the
    displayhook on each ``run_express`` invocation — ``_ensure_installed``
    must layer our shim back on top. Otherwise, bare expressions inside
    ``with``-blocks land in Express's RCM args instead of being routed to
    the active parent."""
    from shinyui import _ctx_stack as cs

    p1 = sui.CtxTag("div", id="a")
    t1 = cs.push(p1)
    try:
        assert sys.displayhook is cs._dispatch
        first_prev = cs._prev_displayhook

        # Simulate an external displayhook swap (Express's RCM enter).
        external_calls: list[object] = []
        external_hook = external_calls.append
        sys.displayhook = external_hook
        assert sys.displayhook is not cs._dispatch

        # Next push must re-install our shim and update _prev_displayhook
        # to the external hook so fall-through routes there.
        p2 = sui.CtxTag("div", id="b")
        t2 = cs.push(p2)
        try:
            assert sys.displayhook is cs._dispatch
            assert cs._prev_displayhook is external_hook
            assert cs._prev_displayhook is not first_prev
        finally:
            cs.pop(t2)
    finally:
        cs.pop(t1)


@pytest.mark.asyncio
async def test_concurrent_tasks_have_isolated_stacks() -> None:
    """Two asyncio tasks each in their own with-block must not pollute each
    other's parent. ContextVar copies at task creation time, so each task
    sees an empty stack at the start and its own parent thereafter."""

    started_a = asyncio.Event()
    started_b = asyncio.Event()
    finish = asyncio.Event()

    card_a: sui.card | None = None
    card_b: sui.card | None = None

    async def task_a() -> None:
        nonlocal card_a
        with sui.card(id="A") as ca:
            card_a = ca
            sys.displayhook(tags.p("a1"))
            started_a.set()
            await started_b.wait()
            sys.displayhook(tags.p("a2"))
            await finish.wait()
            sys.displayhook(tags.p("a3"))

    async def task_b() -> None:
        nonlocal card_b
        await started_a.wait()
        with sui.card(id="B") as cb:
            card_b = cb
            sys.displayhook(tags.p("b1"))
            started_b.set()
            await asyncio.sleep(0)
            sys.displayhook(tags.p("b2"))

    a = asyncio.create_task(task_a())
    b = asyncio.create_task(task_b())
    await b
    finish.set()
    await a

    assert card_a is not None and card_b is not None
    assert len(card_a.children) == 3
    assert all(c.children[0] == f"a{i}" for i, c in enumerate(card_a.children, 1))
    assert len(card_b.children) == 2
    assert all(c.children[0] == f"b{i}" for i, c in enumerate(card_b.children, 1))


def test_expressify_with_blocks_match_positional_form() -> None:
    """The same UI tree built two ways must render structurally identical HTML.

    Positional form: explicit ``card(accordion(panel(slider), ...))`` nesting.
    Express form: ``@expressify`` rewrites bare expression statements into
    ``sys.displayhook(...)`` calls; our shim routes them to the active parent.

    bslib's ``accordion_panel`` generates a random hex suffix
    (``bslib_accordion_panel_<hex>``) on every ``tagify()`` call, so we
    normalise those before comparing to avoid false failures from non-determinism
    that is external to shinyui.
    """
    from shiny.express import expressify

    positional = sui.card(
        sui.accordion(
            sui.accordion_panel("A", sui.input_slider("n", "N", 1, 10, 5)),
            id="acc",
        ),
        id="m",
    )

    @expressify
    def build() -> sui.card:
        with sui.card(id="m") as c:
            with sui.accordion(id="acc"):
                with sui.accordion_panel("A"):
                    sui.input_slider("n", "N", 1, 10, 5)
        return c

    express_form = build()

    def _normalize(html: str) -> str:
        """Replace bslib's random accordion-panel IDs with a fixed placeholder."""
        return re.sub(
            r"bslib_accordion_panel_[0-9a-f]+", "bslib_accordion_panel_X", html
        )

    assert _normalize(str(positional.tagify())) == _normalize(
        str(express_form.tagify())
    )


def test_ctx_tag_with_block_dispatches_to_enclosing_allows_children_parent() -> None:
    """Regression: a ``with CtxTag(...)`` nested inside an ``AllowsChildren``
    parent must propagate itself to the enclosing parent on exit.

    Pre-fix bug (issue #107): ``CtxTag.__exit__`` only popped the stack and
    never forwarded ``self``, so the CtxTag — and the children it had
    collected — were silently dropped from the enclosing tree.
    """
    with sui.card(id="c") as c:
        sys.displayhook(sui.input_slider("n", "N", 1, 10, 5))
        with sui.CtxTag("div", class_="wrapper") as wrapper:
            sys.displayhook(sui.input_slider("m", "M", 1, 10, 5))

    assert len(c.children) == 2
    assert c.children[1] is wrapper
    assert len(wrapper.children) == 1


def test_ctx_tag_with_block_dispatches_to_enclosing_ctx_tag_parent() -> None:
    """A ``with CtxTag(...)`` nested inside another ``with CtxTag(...)``
    must compose into the outer CtxTag's children list."""
    with sui.CtxTag("section") as outer:
        with sui.CtxTag("div") as inner:
            sys.displayhook("hi")

    assert len(outer.children) == 1
    assert outer.children[0] is inner
    assert "hi" in list(inner.children)


def test_ctx_tag_with_block_does_not_dispatch_on_exception() -> None:
    """If the body raises, the CtxTag must not be appended to the enclosing
    parent — matching ``AllowsChildren.__exit__``'s ``exc[0] is None`` guard."""
    with sui.card(id="c") as c:
        try:
            with sui.CtxTag("div"):
                raise RuntimeError("boom")
        except RuntimeError:
            pass

    assert len(c.children) == 0


def test_outermost_with_dispatches_to_prev_displayhook() -> None:
    """When the outermost `with`-block exits with an empty stack, the
    component is forwarded via sys.displayhook so the prior displayhook
    (Express / REPL / Jupyter) can place it. Pre-fix bug: was silently
    dropped.
    """
    from shinyui._ctx_stack import _ensure_installed

    _ensure_installed()

    seen: list[object] = []
    import shinyui._ctx_stack as cs

    original_prev = cs._prev_displayhook
    cs._prev_displayhook = seen.append
    try:
        with sui.card(id="m") as c:
            sys.displayhook(tags.p("inside"))
        # After the with-block exits with an empty stack, `c` itself should
        # have been dispatched to the (previously-installed) displayhook.
        assert c in seen
    finally:
        cs._prev_displayhook = original_prev
