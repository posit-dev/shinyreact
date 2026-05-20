from __future__ import annotations

import shinyuiclassonly as sui


def test_output_plot_tagify_basic():
    o = sui.output_plot("plot")
    html = str(o.tagify())
    assert 'id="plot"' in html


def test_output_plot_carries_interaction_flags():
    o = sui.output_plot("plot", click=True, brush=True, dblclick=True, hover=True)
    assert o.click_enabled is True
    assert o.brush_enabled is True
    assert o.dblclick_enabled is True
    assert o.hover_enabled is True


def test_output_plot_no_value_click_accessor():
    o = sui.output_plot("plot", click=True)
    assert not hasattr(o, "value_click")
    assert not hasattr(o, "value_brush")
    assert not hasattr(o, "value_hover")
    assert not hasattr(o, "value_dbl")


def test_output_plot_is_uioutput():
    o = sui.output_plot("plot")
    assert isinstance(o, sui.UiOutput)
