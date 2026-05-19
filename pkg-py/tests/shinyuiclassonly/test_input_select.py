from __future__ import annotations

import shinyuiclassonly as sui


def test_input_select_tagify_basic():
    s = sui.input_select("c", "Col", {"a": "Alpha", "b": "Beta"})
    html = str(s.tagify())
    assert 'id="c"' in html
    assert "Alpha" in html


def test_input_select_stores_kwargs():
    s = sui.input_select("c", "Col", ["a", "b"], selected="b", multiple=True)
    assert s.id == "c"
    assert s.label == "Col"
    assert s.choices == ["a", "b"]
    assert s._init_selected == "b"
    assert s.multiple is True


def test_input_select_has_no_value_or_update_methods():
    s = sui.input_select("c", "Col", {"a": "A"})
    assert not hasattr(s, "value")
    assert not hasattr(s, "update")


def test_input_select_is_uiinput():
    s = sui.input_select("c", "Col", {"a": "A"})
    assert isinstance(s, sui.UiInput)
