from __future__ import annotations

import shiny.ui as sui
from shinyui._output_plot import output_plot


def test_factory_returns_instance():
    p = output_plot("p", click=True, brush=True)
    assert isinstance(p, output_plot)
    assert p.id == "p"


def test_tagify_matches_shiny_ui_output_plot():
    ours = output_plot("p", click=True, brush=True).tagify()
    theirs = sui.output_plot("p", click=True, brush=True)
    assert ours.get_html_string() == theirs.get_html_string()


def test_flags_forwarded_to_tagify():
    """All four interaction flags + inline are wired into the rendered HTML."""
    p = output_plot(
        "p",
        click=True,
        dblclick=True,
        hover=True,
        brush=True,
        inline=True,
    )
    theirs = sui.output_plot(
        "p",
        inline=True,
        click=True,
        dblclick=True,
        hover=True,
        brush=True,
    )
    assert p.tagify().get_html_string() == theirs.get_html_string()


def test_no_update_method():
    p = output_plot("p")
    assert not hasattr(p, "update")


def test_no_derived_input_accessors_on_output_plot() -> None:
    """Derived-input accessors have moved to shinyui.render_plot."""
    p = output_plot("p", click=True, brush=True)
    for name in ("click_value", "dbl_value", "hover_value", "brush_value"):
        assert not hasattr(p, name), (
            f"output_plot should no longer expose {name}; it lives on render_plot now"
        )


def test_no_render_method_on_output_plot() -> None:
    """output_plot.render was reverted; use @shinyui.render_plot instead."""
    p = output_plot("p")
    assert not hasattr(p, "render")
