from __future__ import annotations

import sys

import shinyui as sui
from htmltools import tags


def test_card_append_mutates_children():
    c = sui.card(id="m")
    c.append(tags.p("hi"))
    assert len(c.children) == 1


def test_card_with_block_collects_via_append():
    with sui.card(id="m") as c:
        c.append(tags.p("inside"))
    assert len(c.children) == 1


def test_accordion_panel_can_be_nested_in_accordion():
    a = sui.accordion(
        sui.accordion_panel("A", tags.p("a-body")),
        sui.accordion_panel("B", tags.p("b-body")),
        id="acc",
    )
    assert len(a.children) == 2


def test_with_block_collects_via_displayhook() -> None:
    """Direct sys.displayhook calls inside a with-block route to the parent."""
    with sui.card(id="m") as c:
        sys.displayhook(tags.p("collected"))
    assert len(c.children) == 1
    assert c.children[0].name == "p"


def test_nested_with_routes_to_innermost_parent() -> None:
    """Nested AllowsChildren context managers form a proper stack."""
    with sui.card(id="m") as c:
        with sui.accordion(id="acc") as acc:
            with sui.accordion_panel("A") as panel:
                sys.displayhook(tags.p("in panel"))
            sys.displayhook(panel)
        sys.displayhook(acc)
    assert len(c.children) == 1 and c.children[0] is acc
    assert len(acc.children) == 1 and acc.children[0] is panel
    assert len(panel.children) == 1
    assert panel.children[0].name == "p"


def test_sequential_with_blocks_do_not_leak() -> None:
    """After exiting a with-block, the stack is fully restored."""
    with sui.card(id="m1") as c1:
        sys.displayhook(tags.p("one"))
    with sui.card(id="m2") as c2:
        sys.displayhook(tags.p("two"))
    assert len(c1.children) == 1
    assert len(c2.children) == 1
    # Stack must be empty after both blocks.
    from shinyui._ctx_stack import _stack
    assert _stack.get() == ()


def test_bare_string_is_collected() -> None:
    """wrap_displayhook_handler coerces bare strings into TagChildren."""
    with sui.card(id="m") as c:
        sys.displayhook("Hello, world!")
    assert c.children == ["Hello, world!"]


def test_none_and_ellipsis_are_filtered() -> None:
    """wrap_displayhook_handler drops None and ... per htmltools semantics."""
    with sui.card(id="m") as c:
        sys.displayhook(None)
        sys.displayhook(...)
        sys.displayhook("kept")
    assert c.children == ["kept"]


def test_exception_in_body_still_pops_stack() -> None:
    """Stack is restored even when the with-block body raises."""
    from shinyui._ctx_stack import _stack

    try:
        with sui.card(id="m") as c:
            sys.displayhook(tags.p("before"))
            raise RuntimeError("intentional")
    except RuntimeError:
        pass
    assert _stack.get() == ()
    assert len(c.children) == 1  # collected before the raise
