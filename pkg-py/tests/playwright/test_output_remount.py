"""Unmounting a hook-based output's last reader unbinds its hidden div (#330).

The registry used to detach the div before Shiny's container-scoped
`unbindAll` ran, which cannot reach a detached element, so each
unmount/remount cycle leaked one Shiny binding for the id. The jsdom unit
test fakes Shiny's bookkeeping; this one runs against the real `shiny.js`.
"""

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

output_remount_app = create_app_fixture("apps/output_remount/app.py")


def test_remounting_an_output_reader_leaks_no_binding(
    page: Page, output_remount_app: ShinyAppProc
) -> None:
    messages: list[str] = []
    page.on("console", lambda msg: messages.append(f"{msg.type}: {msg.text}"))
    page.goto(output_remount_app.url)

    toggle = page.locator("[data-test=toggle]")
    value = page.locator("[data-test=value]")
    expect(value).to_have_text("toggles: 0")

    for n in range(1, 7, 2):
        toggle.click()  # hide: n is odd
        expect(value).to_have_count(0)
        expect(toggle).to_have_text("Show")
        toggle.click()  # show again
        expect(value).to_have_text(f"toggles: {n + 1}")

    offending = [m for m in messages if "Duplicate" in m or "not found" in m]
    assert offending == [], f"leaked output binding: {offending}"
