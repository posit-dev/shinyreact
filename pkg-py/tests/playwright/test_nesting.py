"""E2E proof that "layer all the way down" nesting works in a real browser (#88).

Covers both delivery paths for an interleaved `Node`/htmltools/text tree:
  - static page chrome rendered by the JS `seedInlineSpecs()` pass, and
  - a reactive_output tree delivered over the WebSocket.
"""

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

nesting_app = create_app_fixture("apps/nesting/app.py")


def test_static_node_in_chrome(page: Page, nesting_app: ShinyAppProc) -> None:
    page.goto(nesting_app.url)

    # The static Node in page chrome is rendered by seedInlineSpecs() from the
    # inline <script> emitted by Node.tagify() — no server output involved.
    badge = page.locator('#chrome [data-testid="badge"]')
    expect(badge).to_have_text("static-badge")


def test_reactive_node_interleaves_tags_and_components(
    page: Page, nesting_app: ShinyAppProc
) -> None:
    page.goto(nesting_app.url)

    # The reactive_output returns a Card wrapping a tags.div that interleaves a
    # tags.span ("mixed ") with a nested Badge component, delivered over the
    # WebSocket and rendered into the .shinyreact-output div.
    card = page.locator('[data-testid="card"]')
    expect(card.locator("h2")).to_have_text("Reactive")
    expect(card.locator(".label")).to_have_text("mixed ")
    expect(card.locator('[data-testid="badge"]')).to_have_text("nested-badge")
