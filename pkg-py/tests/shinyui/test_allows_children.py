from __future__ import annotations

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


def test_bare_tag_in_with_block_is_not_auto_collected():
    """Tag-as-CM is sub-issue 3 (out of scope for this prototype)."""
    with sui.card(id="m") as c:
        tags.p("not collected")  # noqa: B018  intentional bare expr
    assert c.children == []
