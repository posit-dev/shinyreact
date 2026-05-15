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
    """Nested AllowsChildren context managers form a proper stack.

    On ``__exit__``, each component auto-dispatches itself to the enclosing
    parent (if one is active), so no explicit ``sys.displayhook`` call is
    needed after the inner ``with`` blocks close.
    """
    with sui.card(id="m") as c:
        with sui.accordion(id="acc") as acc:
            with sui.accordion_panel("A") as panel:
                sys.displayhook(tags.p("in panel"))
            # panel is auto-dispatched to acc on __exit__
        # acc is auto-dispatched to c on __exit__
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


def test_preconstructed_component_works_as_context_manager() -> None:
    """A component built outside any with-block can be entered later.

    `acc = accordion(...)` then `with acc:` is a valid usage pattern — the
    instance is constructed against an empty stack (so it doesn't auto-attach
    to anything), and `__enter__` pushes the already-built instance so its
    body's bare expressions collect into its children.
    """
    acc = sui.accordion(id="acc")
    assert acc.children == []  # constructed empty

    with acc as same_acc:
        assert same_acc is acc
        sys.displayhook(sui.accordion_panel("A"))
        sys.displayhook(sui.accordion_panel("B"))

    assert len(acc.children) == 2
    assert all(isinstance(p, sui.accordion_panel) for p in acc.children)
    assert [p.title for p in acc.children] == ["A", "B"]


def test_preconstructed_with_expressify_form() -> None:
    """Same as above but using @expressify to validate the AST-rewritten path.

    Confirms that defining the parent first and entering it later behaves the
    same under @expressify's bare-expression rewriting as the inline form.
    """
    from shiny.express import expressify

    @expressify
    def build() -> sui.accordion:
        acc = sui.accordion(id="acc")
        with acc:
            sui.accordion_panel("A")
            sui.accordion_panel("B")
        return acc

    acc = build()
    assert len(acc.children) == 2
    assert [p.title for p in acc.children] == ["A", "B"]


def test_with_block_appends_to_existing_positional_children() -> None:
    """Children passed at construction are preserved; with-block adds more.

    A component built with positional children that is later entered as a
    context manager appends — does not replace. Final order:
    positional children first, then with-block children in source order.
    """
    panel_a = sui.accordion_panel("A")
    acc = sui.accordion(panel_a, id="acc")
    assert acc.children == [panel_a]

    with acc:
        sys.displayhook(sui.accordion_panel("B"))
        sys.displayhook(sui.accordion_panel("C"))

    assert len(acc.children) == 3
    assert acc.children[0] is panel_a
    assert [p.title for p in acc.children] == ["A", "B", "C"]


def test_with_block_append_with_expressify() -> None:
    """Same as above, validated through @expressify's AST rewrite."""
    from shiny.express import expressify

    panel_a = sui.accordion_panel("A")

    @expressify
    def extend(parent: sui.accordion) -> sui.accordion:
        with parent:
            sui.accordion_panel("B")
            sui.accordion_panel("C")
        return parent

    acc = extend(sui.accordion(panel_a, id="acc"))
    assert [p.title for p in acc.children] == ["A", "B", "C"]


def test_re_entering_same_instance_keeps_appending() -> None:
    """Entering the same component a second time adds to children again.

    Confirms `with acc:` ... `with acc:` accumulates rather than resetting.
    Not a recommended usage pattern, but the behavior should be predictable.
    """
    acc = sui.accordion(id="acc")
    with acc:
        sys.displayhook(sui.accordion_panel("A"))
    with acc:
        sys.displayhook(sui.accordion_panel("B"))
    assert [p.title for p in acc.children] == ["A", "B"]
