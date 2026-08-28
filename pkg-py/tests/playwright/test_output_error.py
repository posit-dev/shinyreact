from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

output_error_app = create_app_fixture("apps/output-error/app.py")


def test_output_error_message_reaches_the_client(
    page: Page, output_error_app: ShinyAppProc
) -> None:
    """`useShinyOutputError` exposes the server exception's text, so an app can
    reproduce vanilla Shiny's error UI (#257)."""
    page.goto(output_error_app.url)

    value = page.locator("[data-test=value]")
    status = page.locator("[data-test=status]")
    error = page.locator("[data-test=error]")

    expect(value).to_have_text("ok: 1")
    expect(status).to_have_text("ready")
    expect(error).to_be_empty()

    page.locator("[data-test=input]").fill("0")
    expect(error).to_have_text("invalid number of 'breaks'")
    expect(status).to_have_text("error")

    # Recovering clears the error.
    page.locator("[data-test=input]").fill("2")
    expect(value).to_have_text("ok: 2")
    expect(status).to_have_text("ready")
    expect(error).to_be_empty()


def test_silent_error_delivers_no_message(
    page: Page, output_error_app: ShinyAppProc
) -> None:
    """`req()` stays silent: no error message, and the value blanks — matching
    vanilla Shiny, which empties the output element."""
    page.goto(output_error_app.url)

    value = page.locator("[data-test=value]")
    expect(value).to_have_text("ok: 1")

    page.locator("[data-test=input]").fill("-1")
    expect(value).to_be_empty()
    expect(page.locator("[data-test=error]")).to_be_empty()
    expect(page.locator("[data-test=status]")).to_have_text("ready")
