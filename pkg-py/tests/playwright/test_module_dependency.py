import pytest
from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

module_plotly_app = create_app_fixture("apps/module_plotly/app.py")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "set_react_page() does not discover HTMLDependencies from renderers "
        "defined inside @module.server. See "
        "https://github.com/posit-dev/shinyreact/issues/87."
    ),
)
def test_module_renderer_dep_injected(
    page: Page, module_plotly_app: ShinyAppProc
) -> None:
    page.goto(module_plotly_app.url)

    # shinywidgets ships an `ipywidget-output-binding` HTMLDependency that
    # render_plotly attaches. When the renderer lives inside @module.server,
    # set_react_page() never sees it at app-startup time, so the dep is not
    # injected and the plotly chart cannot render.
    expect(
        page.locator("script[src*='ipywidget-output-binding']")
    ).to_be_attached()
