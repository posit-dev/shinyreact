"""End-to-end bookmark restoration tests.

Each test launches the local fixture app under ``apps/bookmark/`` via
py-shiny's app fixture, navigates to a bookmark URL, waits for Shiny to
initialise, and asserts the React-rendered DOM reflects the restored
input values.
"""

from urllib.parse import urlencode

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

bookmark_app = create_app_fixture("apps/bookmark/app.py")


def _wait_for_shiny_initialized(page: Page) -> None:
    """Block until Shiny's initializedPromise has resolved."""
    page.wait_for_function("window.Shiny && window.Shiny.initializedPromise")
    page.evaluate("() => window.Shiny.initializedPromise")


def test_url_mode_restores_inputs(page: Page, bookmark_app: ShinyAppProc) -> None:
    """Navigate to a URL-mode bookmark; inputs and output reflect restored values."""
    # Shiny URL bookmarks encode values as JSON strings:
    #   ?_inputs_&txt=%22hello%22&num=42&chk=true
    qs = "_inputs_&" + urlencode({"txt": '"hello"', "num": "42", "chk": "true"})
    page.goto(f"{bookmark_app.url}?{qs}")
    _wait_for_shiny_initialized(page)

    # React-controlled inputs should show restored values.
    expect(page.get_by_test_id("txt")).to_have_value("hello")
    expect(page.get_by_test_id("num")).to_have_value("42")

    # React tracks checkbox state in JS rather than the DOM `checked` attribute,
    # so verify via JS evaluation rather than to_be_checked().
    checked = page.evaluate("document.querySelector('[data-testid=chk]').checked")
    assert checked is True

    # The server-rendered output should reflect the restored inputs.
    echo = page.get_by_test_id("echo")
    expect(echo).to_contain_text("text='hello'")
    expect(echo).to_contain_text("num=42")
    expect(echo).to_contain_text("checked=yes")


def test_no_bookmark_renders_defaults(page: Page, bookmark_app: ShinyAppProc) -> None:
    """Plain URL renders defaults and the _restore sentinel is applied."""
    page.goto(bookmark_app.url)
    _wait_for_shiny_initialized(page)

    # Default values from app.js: txt="", num=0, chk=false.
    expect(page.get_by_test_id("txt")).to_have_value("")
    expect(page.get_by_test_id("num")).to_have_value("0")

    checked = page.evaluate("document.querySelector('[data-testid=chk]').checked")
    assert checked is False

    # After shinyreact initialises without restore data the sentinel should show
    # an applied-but-empty state.
    sentinel = page.evaluate("JSON.stringify(window.shinyreact._restore)")
    assert sentinel == '{"-applied":true,"-values":{}}'


# Round-trip server-stored bookmarking (set inputs → click bookmark → reload
# at the new ``?_state_id_=...`` URL → assert restored React state) needs a
# second fixture with ``bookmark_store="server"`` that can be spawned
# alongside the existing URL-mode fixture. py-shiny's ``create_app_fixture``
# does not yet expose a per-test override hook for app options, so the
# test is omitted entirely until that lands. The Python-side emission for
# server mode is already covered by ``test_bookmark_restore.py`` unit tests
# (which drive the same ``RestoreContext`` machinery the server-stored path
# would produce).
#
# def test_server_mode_round_trip(page: Page, server_bookmark_app: ShinyAppProc):
#     page.goto(server_bookmark_app.url)
#     ...inputs.fill, bookmark-btn click, capture _state_id_, reload, assert...
