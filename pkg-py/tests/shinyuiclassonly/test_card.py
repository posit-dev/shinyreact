from __future__ import annotations

import shinyuiclassonly as sui
from htmltools import tags


def test_card_tagify_basic():
    c = sui.card(tags.p("hi"), id="m")
    rendered = c.tagify()
    assert "shiny-html-output" not in str(rendered)  # not an output
    assert "main" not in str(rendered)  # placeholder check on id quirk


def test_card_id_optional():
    """shinyuiclassonly does not require id on layouts (no accessors to wire)."""
    c = sui.card(tags.p("hi"))
    assert c.id is None
    c.tagify()  # must render


def test_card_stores_full_screen_flag():
    c = sui.card(id="m", full_screen=True)
    assert c._full_screen is True


def test_card_collects_children_via_with():
    import sys

    with sui.card(id="m") as c:
        sys.displayhook(tags.p("inside"))
    assert len(c.children) == 1
    assert c.children[0].name == "p"


def test_card_positional_children():
    c = sui.card(tags.p("a"), tags.p("b"), id="m")
    assert len(c.children) == 2


def test_card_has_no_value_or_update_methods():
    """shinyuiclassonly strips accessors and update()."""
    c = sui.card(id="m")
    assert not hasattr(c, "value_full_screen")
    assert not hasattr(c, "update")


def test_card_is_uilayout_and_allows_children():
    c = sui.card(id="m")
    assert isinstance(c, sui.UiLayout)
    assert isinstance(c, sui.AllowsChildren)
