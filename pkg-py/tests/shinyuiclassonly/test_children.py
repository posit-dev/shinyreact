from __future__ import annotations

import sys

from htmltools import tags
from shinyuiclassonly._base import UiComponent
from shinyuiclassonly._children import AllowsChildren


class _ChildBox(UiComponent, AllowsChildren):
    def tagify(self):
        return tags.div(*self.children)


def test_children_default_empty():
    b = _ChildBox()
    assert b.children == []


def test_children_from_positional_args():
    b = _ChildBox("a", "b")
    assert b.children == ["a", "b"]


def test_append_returns_self_and_mutates():
    b = _ChildBox()
    r = b.append("x")
    assert r is b
    assert b.children == ["x"]


def test_with_block_returns_self_and_collects_via_displayhook():
    with _ChildBox() as b:
        sys.displayhook(tags.p("inside"))
    assert len(b.children) == 1
    assert b.children[0].name == "p"


def test_with_block_returns_self_and_collects_via_append():
    with _ChildBox() as b:
        b.append("inside")
    assert b.children == ["inside"]


def test_outermost_with_dispatches_to_prev_displayhook():
    """When the outermost `with`-block exits with an empty stack, the
    component is forwarded via sys.displayhook so the prior displayhook
    (Express / REPL) can place it.
    """
    from shinyuiclassonly._ctx_stack import _ensure_installed

    _ensure_installed()

    seen: list[object] = []
    import shinyuiclassonly._ctx_stack as cs

    original_prev = cs._prev_displayhook
    cs._prev_displayhook = seen.append
    try:
        with _ChildBox() as b:
            sys.displayhook(tags.p("inside"))
        assert b in seen
    finally:
        cs._prev_displayhook = original_prev
