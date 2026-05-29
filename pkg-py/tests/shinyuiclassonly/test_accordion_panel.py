from __future__ import annotations

import shinyuiclassonly as sui


def test_accordion_panel_value_defaults_to_title():
    p = sui.accordion_panel("Settings")
    assert p.value == "Settings"


def test_accordion_panel_value_can_override():
    p = sui.accordion_panel("Settings", value="settings_v")
    assert p.value == "settings_v"


def test_accordion_panel_tagify():
    p = sui.accordion_panel("A", "body text")
    rendered = p.tagify()
    assert rendered is not None


def test_accordion_panel_collects_children_via_with():
    import sys

    from htmltools import tags

    with sui.accordion_panel("Settings") as p:
        sys.displayhook(tags.p("hi"))
    assert len(p.children) == 1
    assert p.children[0].name == "p"


def test_accordion_panel_has_no_value_or_update_methods():
    """`value` is a property returning the title fallback string — it is
    NOT a session-aware accessor here (shinyui's panel has no accessor
    either, but the equivalent value() is on its parent accordion)."""
    p = sui.accordion_panel("A")
    assert isinstance(p.value, str)
    assert not hasattr(p, "update")
