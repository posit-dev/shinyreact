"""Layer A: _react_page_fn harvests deps from renderers registered on the
session, including those inside @module.server (issue #87)."""

from __future__ import annotations

from htmltools import HTMLDependency, TagList, div
from shiny.express._stub_session import ExpressStubSession
from shiny.render.renderer import Renderer
from shiny.session import session_context
from shinyreact._page import _build_react_page_fn


def _make_widget_renderer(dep: HTMLDependency) -> type[Renderer]:
    class render_widget(Renderer):  # noqa: N801
        def auto_output_ui(self):
            return div(dep, id=self.output_id, class_="my-widget-output")

        async def transform(self, value):  # pragma: no cover - not exercised
            return value

    return render_widget


def test_react_page_harvests_session_output_deps(tmp_path) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")

    dep = HTMLDependency("widget-x", "1.0", source={"subdir": str(tmp_path)})
    render_widget = _make_widget_renderer(dep)

    page_fn = _build_react_page_fn(index)

    stub = ExpressStubSession()
    with session_context(stub):
        # Register a renderer the way @module.server would — it lands in
        # stub.output._outputs but is NOT passed to page_fn as an arg.
        @stub.output
        @render_widget
        def thing():  # pragma: no cover - never rendered
            return "x"

        result = page_fn()  # no *args, mirroring a module-only renderer

    dep_names = [d.name for d in TagList(result).get_dependencies()]
    assert "widget-x" in dep_names
