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


def test_render_returns_renderer_bound_to_id() -> None:
    """output_code.render(fn) returns a Renderer whose output_id is the
    output's id, not the function's __name__."""
    import shinyui as sui_pkg
    from shiny.render.renderer import Renderer

    out = sui_pkg.output_code("summary")

    @out.render
    def _():
        return "ok"

    assert isinstance(_, Renderer)
    assert _.output_id == "summary"


def test_render_overrides_function_name() -> None:
    """The function passed to .render is renamed to match the output id."""
    import shinyui as sui_pkg

    out = sui_pkg.output_code("summary")

    def my_renderer():
        return "ok"

    out.render(my_renderer)
    assert my_renderer.__name__ == "summary"
