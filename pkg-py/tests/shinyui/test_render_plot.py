"""Tests for shinyui.render_plot — plot renderer with derived-input accessors.

Mock-session tests for the accessors; we don't run an actual plot renderer.
"""

from __future__ import annotations

import shinyui as sui
from shiny import reactive
from shiny.render.renderer import Renderer


def test_render_plot_is_a_renderer():
    @sui.render_plot(click=True, brush=True)
    def my_plot() -> None:
        return None

    assert isinstance(my_plot, Renderer)


def test_render_plot_auto_output_ui_emits_output_plot_with_flags():
    @sui.render_plot(click=True, brush=True)
    def my_plot() -> None:
        return None

    tag = my_plot.auto_output_ui()
    html = str(tag)
    # The output_plot id and the click/brush flags should be present.
    assert "my_plot" in html
    # Reference: the same flags through shinyui.output_plot should produce
    # the same HTML.
    import shiny.ui as _sui

    expected = _sui.output_plot("my_plot", click=True, brush=True).get_html_string()
    assert tag.get_html_string() == expected


def test_render_plot_click_value_reads_correct_input(mock_session):
    @sui.render_plot(click=True)
    def my_plot() -> None:
        return None

    mock_session.input.__getitem__.return_value = lambda: {"x": 10, "y": 20}
    with reactive.isolate():
        assert my_plot.click_value() == {"x": 10, "y": 20}
    mock_session.input.__getitem__.assert_called_with("my_plot_click")


def test_render_plot_brush_value_reads_correct_input(mock_session):
    @sui.render_plot(brush=True)
    def my_plot() -> None:
        return None

    mock_session.input.__getitem__.return_value = lambda: {"xmin": 1, "xmax": 2}
    with reactive.isolate():
        assert my_plot.brush_value() == {"xmin": 1, "xmax": 2}
    mock_session.input.__getitem__.assert_called_with("my_plot_brush")


def test_render_plot_hover_and_dbl_values(mock_session):
    @sui.render_plot(hover=True, dblclick=True)
    def my_plot() -> None:
        return None

    seq = iter([{"x": 1}, {"x": 2}])
    mock_session.input.__getitem__.return_value = lambda: next(seq)
    with reactive.isolate():
        assert my_plot.hover_value() == {"x": 1}
        assert my_plot.dbl_value() == {"x": 2}
