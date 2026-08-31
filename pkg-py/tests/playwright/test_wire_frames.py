"""e2e coverage for `shinyreact.playwright.WireTap` against a real app.

Because shinyreact's client/server contract is plain JSON on the websocket,
an app author can pin the *semantics* of an output (which column, which
units) against the actual bytes the server sent — an oracle independent of
both the React code and the server code that produced them. The unit-level
counterpart (fake page, no browser) is pkg-py/tests/test_wire_tap.py; the R
counterpart of this file is pkg-r/tests/testthat/test-wire-tap.R plus the
shinytest2 walkthrough in spikes/201-wire-verification/.

Demo target: examples/01-hello (Old Faithful). The `waiting` column spans
~43–96 minutes; the `eruptions` column spans ~1.6–5.1. Asserting on
`breaks[0]` distinguishes the two columns outright.
"""

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc
from shinyreact.playwright import WireTap

hello_app = create_app_fixture("../../../examples/01-hello/app.py")


def test_histogram_wire_payload_uses_waiting_column(
    page: Page, hello_app: ShinyAppProc
) -> None:
    tap = WireTap(page)
    page.goto(hello_app.url)

    # --- client -> server: the untyped input rides the shinyreact.default
    # handler, and the first delivered value is the hook's defaultValue (30).
    tap.expect_input_value("bins", 30)

    # --- server -> client: dist_data is the histogram of the *waiting*
    # column. waiting spans ~43–96 min; eruptions spans ~1.6–5.1 min, so the
    # first break alone proves which column was binned. Every faithful.csv
    # row lands in a bin.
    tap.expect_output_value(
        "dist_data",
        lambda d: (
            d["breaks"][0] == 43.0
            and 90 <= d["breaks"][-1] <= 100
            and sum(d["counts"]) == 272
        ),
    )

    # --- reactivity: moving the slider re-sends the input and produces a
    # fresh payload with the requested bin count. The cursor guarantees these
    # match strictly later values than the ones matched above.
    page.locator("input[type=range]").fill("5")
    expect(page.locator(".caption")).to_contain_text("5 bins")
    tap.expect_input_value("bins", 5)
    tap.expect_output_value("dist_data", lambda d: len(d["counts"]) == 5)

    # 01-hello uses no send_message(); the channel history is simply empty.
    assert tap.all_messages("notify") == []
