from __future__ import annotations

from htmltools import tags
from shinyui._base import UiComponent
from shinyui._children import AllowsChildren


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


def test_with_block_returns_self_and_collects_via_append():
    with _ChildBox() as b:
        b.append("inside")
    assert b.children == ["inside"]


def test_enter_does_not_raise():
    # Inherits from UiComponent (which raises), but AllowsChildren overrides.
    b = _ChildBox()
    # Should not raise:
    assert b.__enter__() is b
