"""How a renderer's HTMLDependency reaches the browser, one test per path.

Three delivery paths, and which one a given app gets depends on *when* the
renderer registers and whether the output element comes from the server:

| registers at | element from | delivery path                          |
| ------------ | ------------ | -------------------------------------- |
| page-gen     | React        | `set_react_page()` harvest -> `<head>` |
| after load   | `@render.ui` | Shiny dynamic-UI (renderContent)       |
| after load   | React        | shinyreact post-flush push (#220)      |

The last two both register late, so *lateness* is not what separates them —
who emits the output element is. The holder test below passes with
`install_dep_discovery()` stubbed out; the no-holder test does not. That is
the discriminator, and it is why the no-holder fixture is the one that proves
the push is required.
"""

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


def test_late_dep_with_a_server_side_holder(
    page: Page, dynamic_plotly_app: ShinyAppProc
) -> None:
    """Late renderer + `@render.ui` holder: Shiny's own dynamic-UI path covers it.

    The fixture registers `scatter` inside a `@reactive.effect`, so the
    page-generation harvest cannot pre-inject its dependency into `<head>` —
    the served-HTML assertion below pins that down. The output element then
    comes from the *server* (`@render.ui` → `output_widget()`), so Shiny sends
    `{html, deps}` and its client loads the dep via renderContent →
    renderDependencies.

    Two paths therefore deliver it here — that one and shinyreact's post-flush
    push (#220) — which is exactly why this test cannot prove the push is
    required: it passes with `install_dep_discovery()` stubbed out. See
    `test_late_dep_without_a_holder` for the case that cannot.
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


def test_late_dep_without_a_holder(
    page: Page, late_data_frame_app: ShinyAppProc
) -> None:
    """Late renderer + React-emitted element: the post-flush push is the only path.

    "Open a tab whose outputs don't exist yet": `grid` is registered only when
    the user clicks, so the page-generation harvest never sees it. Unlike
    `apps/dynamic_plotly` the output element is emitted by **React**, not by a
    server-side `@render.ui` holder, so Shiny never sends HTML for it and its
    dynamic-UI dependency path never runs. Only shinyreact's flush-diff push
    can deliver `data-frame.js`; stub `install_dep_discovery()` out and this
    test fails while its holder-based sibling still passes.

    Not a widget fixture on purpose: shinywidgets' `comm_open` arrives on its
    own channel and races the dep load (#160), so a holder-less plotly output
    would not be a clean proof even with the push working.
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
