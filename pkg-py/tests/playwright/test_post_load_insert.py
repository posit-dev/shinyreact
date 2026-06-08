"""E2E proof for #120: static `.shinyreact-static` mounts inserted after page
load are not seeded.

`test_static_chrome_seeds_at_load` is the control — it confirms the one-shot
`seedInlineSpecs()` pass renders static mounts present at load.

`test_dynamic_node_via_render_ui_seeds` is the regression test. It FAILS today:
the `@render.ui` Node tagifies into a `.shinyreact-static` mount that is
inserted over the WebSocket after `DOMContentLoaded`, so the one-shot seeding
pass never renders it. The mount is attached to the DOM but empty. After the
fix (MutationObserver-based seeding), the badge renders and this passes.
"""

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

app = create_app_fixture("apps/post_load_insert/app.py")


def test_static_chrome_seeds_at_load(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    # Control: a static Node present in page chrome at load IS seeded.
    badge = page.locator('#chrome [data-testid="badge"]')
    expect(badge).to_have_text("static-badge")


def test_dynamic_node_via_render_ui_seeds(page: Page, app: ShinyAppProc) -> None:
    page.goto(app.url)

    # Wait for the control badge so we know the page is fully booted/seeded.
    expect(page.locator('#chrome [data-testid="badge"]')).to_have_text("static-badge")

    # #panel starts empty; clicking inserts a Node-bearing static mount over
    # the WebSocket, AFTER the one-shot DOMContentLoaded seeding pass.
    page.get_by_role("button", name="Show panel").click()

    # The static mount is inserted into the DOM...
    expect(page.locator("#panel .shinyreact-static")).to_be_attached()

    # ...and SHOULD render its Badge. This is the bug: it does not today.
    badge = page.locator('#panel [data-testid="badge"]')
    expect(badge).to_have_text("dynamic-badge")
