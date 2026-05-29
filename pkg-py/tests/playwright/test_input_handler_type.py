from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

input_handler_app = create_app_fixture("apps/input-handler-type/app.py")


def test_shiny_datetime_handler_runs_on_server(
    page: Page, input_handler_app: ShinyAppProc
) -> None:
    """`type='shiny.datetime'` routes the input through Shiny's datetime handler,
    so `input.when()` resolves to a `datetime.datetime` server-side."""
    page.goto(input_handler_app.url)

    echo = page.locator("[data-test=echo]")
    # The handler runs on the first delivered value; the rendered text should
    # be "datetime", not "int".
    expect(echo).to_have_text("datetime")

    # Change the number — handler still runs; type stays "datetime".
    page.locator("[data-test=input]").fill("1731436800")
    page.locator("[data-test=input]").press("Tab")
    expect(echo).to_have_text("datetime")
