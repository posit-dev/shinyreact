from __future__ import annotations

import shinyuiclassonly as sui


def test_input_slider_tagify_basic():
    s = sui.input_slider("n", "N", 1, 10, 5)
    html = str(s.tagify())
    assert 'id="n"' in html


def test_input_slider_stores_kwargs():
    s = sui.input_slider("n", "N", 0, 100, 50, step=5, ticks=True)
    assert s.id == "n"
    assert s.label == "N"
    assert s.min == 0
    assert s.max == 100
    assert s._init_value == 50
    assert s.step == 5
    assert s.ticks is True


def test_input_slider_has_no_value_or_update_methods():
    s = sui.input_slider("n", "N", 1, 10, 5)
    assert not hasattr(s, "value")
    assert not hasattr(s, "update")


def test_input_slider_is_uiinput():
    s = sui.input_slider("n", "N", 1, 10, 5)
    assert isinstance(s, sui.UiInput)
    assert isinstance(s, sui.UiComponent)
    assert not isinstance(s, sui.AllowsChildren)
