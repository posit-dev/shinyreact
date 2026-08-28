import re

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

    The fixture registers `scatter` inside a `@reactive.effect` so the renderer
    is not on the session at page-generation time — the page-generation harvest
    cannot pre-inject its dependency into <head>, which the served-HTML
    assertion below pins down. Two paths then deliver it: shinyreact's
    post-flush push (#220), and Shiny's own dynamic-UI path
    (renderContent → renderDependencies) when the holder renders.
    """
    # `lib/` prefix, not the bare name: the fixture's own explainer paragraph
    # mentions the dependency by name.
    assert "lib/ipywidget-output-binding" not in page.request.get(
        dynamic_plotly_app.url
    ).text()

    page.goto(dynamic_plotly_app.url)

    expect(page.locator("#show")).to_be_attached()

    page.locator("#show").check()

    # The ipywidgets binding dependency must be loaded...
    expect(
        page.locator("script[src*='ipywidget-output-binding']").first
    ).to_be_attached()
    # ...and the Plotly chart must actually render inside the dynamic holder.
    expect(page.locator("#holder .plotly").first).to_be_attached()


late_data_frame_app = create_app_fixture("apps/late_data_frame/app.py")


def test_late_renderer_dep_is_pushed_after_flush(
    page: Page, late_data_frame_app: ShinyAppProc
) -> None:
    """The post-flush dep push (#220) is the only delivery path here.

    "Open a tab whose outputs don't exist yet": `grid` is registered only when
    the user clicks, so `set_react_page()`'s page-generation harvest never sees
    it, and — unlike `apps/dynamic_plotly` — there is no `@render.ui` holder,
    so Shiny's dynamic-UI dependency path never runs either. Without
    shinyreact's flush-diff push, `data-frame.js` never reaches the browser and
    `<shiny-data-frame>` stays an empty, unbound custom element.
    """
    page.goto(late_data_frame_app.url)

    # Nothing registered yet on either side: no output element, and no binding
    # script anywhere on the page.
    expect(page.locator("#add")).to_be_attached()
    expect(page.locator("shiny-data-frame")).to_have_count(0)
    expect(page.locator("script[src*='data-frame.js']")).to_have_count(0)

    page.locator("#add").click()

    grid = page.locator("[data-test=container] > shiny-data-frame")
    expect(grid).to_be_attached()
    # Binding present (pushed dep loaded + bindAll re-run)...
    expect(grid).to_have_class(re.compile(r"\bshiny-bound-output\b"))
    # ...and the value actually rendered through it.
    expect(grid.get_by_text("alpha")).to_be_attached()
