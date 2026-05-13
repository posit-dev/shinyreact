from __future__ import annotations

import shiny.ui as sui
from shinyui._output_code import UiOutputCode, output_code


def test_factory_returns_instance():
    o = output_code("summary")
    assert isinstance(o, UiOutputCode)
    assert o.id == "summary"


def test_tagify_matches_shiny_ui_output_code():
    ours = output_code("summary").tagify()
    theirs = sui.output_code("summary")
    assert ours.get_html_string() == theirs.get_html_string()
