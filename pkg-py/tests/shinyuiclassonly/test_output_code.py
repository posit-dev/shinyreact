from __future__ import annotations

import shinyuiclassonly as sui


def test_output_code_tagify_basic():
    o = sui.output_code("summary")
    html = str(o.tagify())
    assert 'id="summary"' in html


def test_output_code_default_placeholder():
    o = sui.output_code("summary")
    assert o.placeholder is True


def test_output_code_placeholder_false():
    o = sui.output_code("summary", placeholder=False)
    assert o.placeholder is False


def test_output_code_is_uioutput():
    o = sui.output_code("summary")
    assert isinstance(o, sui.UiOutput)
    assert not isinstance(o, sui.UiInput)
