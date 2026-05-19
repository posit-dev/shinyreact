from __future__ import annotations

import shinyuiclassonly as sui


def test_render_plot_extends_shiny_render_plot():
    from shiny.render._render import plot as _shiny_plot

    assert issubclass(sui.render_plot, _shiny_plot)


def test_render_plot_carries_flags():
    @sui.render_plot(click=True, brush=True)
    def _plot():
        return None

    assert _plot.click_enabled is True
    assert _plot.brush_enabled is True
    assert _plot.dblclick_enabled is False
    assert _plot.hover_enabled is False


def test_render_plot_auto_output_ui_returns_output_plot_instance():
    """auto_output_ui must return a shinyuiclassonly.output_plot instance
    (Tagifiable), NOT a tagified Tag."""

    @sui.render_plot(click=True, brush=True)
    def _plot():
        return None

    _plot.output_id = "plot"  # shiny.render.plot sets this via metadata; emulate
    placeholder = _plot.auto_output_ui()
    assert isinstance(placeholder, sui.output_plot)
    assert placeholder.click_enabled is True
    assert placeholder.brush_enabled is True


def test_render_plot_has_no_session_accessors():
    @sui.render_plot()
    def _plot():
        return None

    assert not hasattr(_plot, "click_value")
    assert not hasattr(_plot, "brush_value")
    assert not hasattr(_plot, "dbl_value")
    assert not hasattr(_plot, "hover_value")
