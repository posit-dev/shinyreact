"""Real Shiny input widgets hosted inside a `ui.tsx` client (issue #286).

`ShinyOutput` alone calls only `Shiny.bindAll()`, which is enough for an
output but not for an input — an input binding also needs its `initialize()`
pass, and the widget's own `HTMLDependency` (ion-rangeslider, selectize) has
to reach the page. Shiny's html-output binding does both: `renderContent()`
loads the dependencies, then calls `initializeInputs()` *and* `bindAll()`.
So a `@render.ui` holder inside `<ShinyOutput className="shiny-html-output">`
hosts a real widget with no new component.
"""

import re

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

dynamic_input_app = create_app_fixture("apps/dynamic_input/app.py")


def test_hosted_slider_and_selectize_are_real_widgets(
    page: Page, dynamic_input_app: ShinyAppProc
) -> None:
    page.goto(dynamic_input_app.url)

    # ion-rangeslider really initialized: the plugin inserts its own DOM next
    # to the bare `<input>` and marks the input bound. Without
    # `initializeInputs()` neither would happen, and `input.bins()` would
    # never arrive.
    expect(page.locator("#widgets .irs--shiny")).to_be_visible()
    expect(page.locator("#bins")).to_have_class(
        re.compile(r"\bshiny-bound-input\b"),
    )
    expect(page.locator(".irs-single")).to_have_text("9")

    # selectize likewise swaps in its own control.
    expect(page.locator(".selectize-control .selectize-input")).to_contain_text("a")

    # And the values reach the server as a classic Shiny app's would.
    expect(page.locator("#echo-view")).to_have_text('{"bins":9,"letter":"a"}')


def test_hosted_widgets_accept_server_side_updates(
    page: Page, dynamic_input_app: ShinyAppProc
) -> None:
    page.goto(dynamic_input_app.url)
    expect(page.locator("#echo-view")).to_have_text('{"bins":9,"letter":"a"}')

    # `update_slider()` / `update_selectize()` target the hosted widgets by id
    # exactly as in a classic app, and the new values flow back through
    # `input`.
    page.locator("#bump").click()
    expect(page.locator("#echo-view")).to_have_text('{"bins":42,"letter":"c"}')
    expect(page.locator(".irs-single")).to_have_text("42")


def test_hosted_slider_drives_the_server_when_dragged(
    page: Page, dynamic_input_app: ShinyAppProc
) -> None:
    page.goto(dynamic_input_app.url)
    expect(page.locator(".irs-single")).to_have_text("9")

    # Click the far right of the slider track: ionRangeSlider moves the handle
    # to the max, and the input change reaches the server.
    bar = page.locator(".irs-line")
    box = bar.bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + box["width"] - 1, box["y"] + box["height"] / 2)

    expect(page.locator("#echo-view")).to_have_text('{"bins":50,"letter":"a"}')
