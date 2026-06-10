from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

module_plotly_app = create_app_fixture("apps/module_plotly/app.py")


def test_module_renderer_dep_injected(
    page: Page, module_plotly_app: ShinyAppProc
) -> None:
    page.goto(module_plotly_app.url)

    # shinywidgets ships an `ipywidget-output-binding` HTMLDependency that
    # render_plotly attaches. With the session-output harvest, set_react_page()
    # now finds it even though the renderer lives inside @module.server.
    # (The dependency adds multiple <script> tags, so use .first to avoid
    # Playwright's strict-mode violation when >1 match is found.)
    expect(
        page.locator("script[src*='ipywidget-output-binding']").first
    ).to_be_attached()
