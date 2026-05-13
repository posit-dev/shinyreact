from __future__ import annotations

import shiny.ui as sui
from shiny import reactive
from shinyui._output_plot import UiOutputPlot, output_plot


def test_factory_returns_instance():
    p = output_plot("p", click=True, brush=True)
    assert isinstance(p, UiOutputPlot)
    assert p.id == "p"


def test_tagify_matches_shiny_ui_output_plot():
    ours = output_plot("p", click=True, brush=True).tagify()
    theirs = sui.output_plot("p", click=True, brush=True)
    assert ours.get_html_string() == theirs.get_html_string()


def test_click_value_reads_correct_id(mock_session):
    p = output_plot("p", click=True)
    mock_session.input.__getitem__.return_value = lambda: {"x": 10, "y": 20}
    with reactive.isolate():
        assert p.click_value() == {"x": 10, "y": 20}
    mock_session.input.__getitem__.assert_called_with("p_click")


def test_brush_value_reads_correct_id(mock_session):
    p = output_plot("p", brush=True)
    mock_session.input.__getitem__.return_value = lambda: {"xmin": 1, "xmax": 2}
    with reactive.isolate():
        assert p.brush_value() == {"xmin": 1, "xmax": 2}
    mock_session.input.__getitem__.assert_called_with("p_brush")


def test_hover_and_dbl_values(mock_session):
    p = output_plot("p", hover=True, dblclick=True)
    seq = iter([{"x": 1}, {"x": 2}])
    mock_session.input.__getitem__.return_value = lambda: next(seq)
    with reactive.isolate():
        assert p.hover_value() == {"x": 1}
        assert p.dbl_value() == {"x": 2}


def test_no_update_method():
    p = output_plot("p")
    assert not hasattr(p, "update")
