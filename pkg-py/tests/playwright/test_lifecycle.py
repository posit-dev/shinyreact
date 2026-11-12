"""Shiny fires its lifecycle events through jQuery's `trigger()`, which never
reaches an `addEventListener()` listener. These run against real Shiny, since
the jsdom tests can only send native events (#328)."""

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

lifecycle_app = create_app_fixture("apps/lifecycle/app.py")


def test_use_shiny_busy_follows_a_slow_output(
    page: Page, lifecycle_app: ShinyAppProc
) -> None:
    page.goto(lifecycle_app.url)
    busy = page.locator("[data-test=busy]")
    expect(page.locator("[data-test=connected]")).to_have_text("true")
    expect(busy).to_have_text("false")

    page.locator("[data-test=slow]").click()
    expect(busy).to_have_text("true")
    expect(page.locator("[data-test=slow-value]")).to_have_text("1")
    expect(busy).to_have_text("false")


def test_use_shiny_connected_turns_false_when_the_session_closes(
    page: Page, lifecycle_app: ShinyAppProc
) -> None:
    page.goto(lifecycle_app.url)
    connected = page.locator("[data-test=connected]")
    expect(connected).to_have_text("true")

    page.locator("[data-test=close]").click()
    expect(connected).to_have_text("false")
