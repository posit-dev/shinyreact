"""A protocol handshake failure must be readable without opening DevTools.

The handshake throws during the first hook mount, so nothing the app renders
survives — before #213 the only artifact was a console message on a blank
page. The fixture app under ``apps/protocol_mismatch/`` claims protocol
``999.0``; the client should paint the mismatch onto the page.
"""

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc
from shinyreact._protocol import PROTOCOL_VERSION

mismatch_app = create_app_fixture("apps/protocol_mismatch/app.py")


def test_mismatch_paints_a_banner(page: Page, mismatch_app: ShinyAppProc) -> None:
    page.goto(mismatch_app.url)

    banner = page.locator("#shinyreact-fatal-error")
    expect(banner).to_be_visible()
    # Both versions and the remedy, matching the thrown error.
    expect(banner).to_contain_text("999.0")
    expect(banner).to_contain_text(PROTOCOL_VERSION)
    expect(banner).to_contain_text("Upgrade the older side")
    expect(banner).to_have_attribute("role", "alert")

    # Both versions are marked up as <code> so they stand out from the prose.
    expect(banner.locator("code")).to_have_text(["999.0", PROTOCOL_VERSION])

    # Fail fast is unchanged: the app body never rendered.
    expect(page.get_by_test_id("body")).to_have_count(0)
