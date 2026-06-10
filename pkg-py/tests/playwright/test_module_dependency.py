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


dynamic_plotly_app = create_app_fixture("apps/dynamic_plotly/app.py")


def test_dynamic_ui_plotly_dep(page: Page, dynamic_plotly_app: ShinyAppProc) -> None:
    """Checkbox-gated Plotly chart via @render.ui → output_widget mounts natively.

    Shiny's own dynamic-UI path (renderContent → renderDependencies) delivers the
    ipywidget-output-binding dependency to the client when the holder renders, so
    Layer B (flush-diff dep push) is not needed for this case.
    """
    page.goto(dynamic_plotly_app.url)

    page.locator("#show").check()

    # The ipywidgets binding dependency must be loaded...
    expect(
        page.locator("script[src*='ipywidget-output-binding']").first
    ).to_be_attached()
    # ...and the Plotly chart must actually render inside the dynamic holder.
    expect(page.locator("#holder .plotly").first).to_be_attached()
