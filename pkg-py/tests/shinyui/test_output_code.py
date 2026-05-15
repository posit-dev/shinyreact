from __future__ import annotations

import shiny.ui as sui
from shinyui._output_code import output_code


def test_factory_returns_instance():
    o = output_code("summary")
    assert isinstance(o, output_code)
    assert o.id == "summary"


def test_tagify_matches_shiny_ui_output_code():
    ours = output_code("summary").tagify()
    theirs = sui.output_code("summary")
    assert ours.get_html_string() == theirs.get_html_string()


def test_no_render_method_on_output_code() -> None:
    """output_code.render was reverted; use bare @render.code instead."""
    o = output_code("summary")
    assert not hasattr(o, "render")
