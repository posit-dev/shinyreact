import re

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

classname_app = create_app_fixture("apps/classname/app.py")
data_frame_app = create_app_fixture("apps/data_frame/app.py")
plotly_app = create_app_fixture("apps/plotly/app.py")


def test_custom_classname_lands_on_rendered_element(
    page: Page, classname_app: ShinyAppProc
) -> None:
    page.goto(classname_app.url)

    out = page.locator("#out")
    # `to_be_attached()` (not `to_be_visible()`): the rendered element has no
    # content, so its box is 0×0 and Playwright would consider it "hidden".
    # We only care about presence + classes + attributes here.
    expect(out).to_be_attached()

    # `<ShinyOutput>` does not add classes of its own — caller-supplied classes
    # must be present. (Shiny's binding pass adds `shiny-bound-output` after
    # mount; the regexes below are deliberately tolerant of that extra class.)
    expect(out).to_have_class(re.compile(r"\bcustom-a\b"))
    expect(out).to_have_class(re.compile(r"\bcustom-b\b"))

    # And the binding pass really did run: `shiny-bound-output` was only ever
    # described in a comment, asserted nowhere, so nothing caught a regression
    # where the element rendered but never bound.
    expect(out).to_have_class(re.compile(r"\bshiny-bound-output\b"))

    # Arbitrary HTML attributes pass through to the rendered element.
    expect(out).to_have_attribute("data-test-marker", "x")

    # Direct-child assertion: `>` combinator fails if any wrapper sneaks in.
    expect(page.locator("[data-test=container] > #out")).to_be_attached()

    # Computed-style guard for the same regression: the index.html `<style>`
    # block paints `[data-test=container] > * { outline: 3px solid hotpink }`.
    # A wrapper would steal that match, leaving `#out` at its default outline.
    expect(out).to_have_css("outline-style", "solid")
    expect(out).to_have_css("outline-color", "rgb(255, 105, 180)")


def test_data_frame_renders_inside_shiny_output(
    page: Page, data_frame_app: ShinyAppProc
) -> None:
    page.goto(data_frame_app.url)

    table = page.locator("shiny-data-frame#my_table")
    expect(table).to_be_visible()

    # Smoke check: the binding fired and at least one cell from the dataframe
    # rendered. The frame is `{"a": [1, 2], "b": [3, 4]}` — "1" appears as the
    # first value of column "a".
    expect(table).to_contain_text("1")

    # Direct-child assertion: no wrapper between `<div data-test="container">`
    # and the rendered `<shiny-data-frame>` element.
    expect(
        page.locator("[data-test=container] > shiny-data-frame#my_table")
    ).to_be_attached()

    # Computed-style guard: the container CSS paints a hot-pink outline on
    # direct children only. A wrapper regression would strand the table at
    # the default outline.
    expect(table).to_have_css("outline-style", "solid")
    expect(table).to_have_css("outline-color", "rgb(255, 105, 180)")


def test_plotly_renders_inside_shiny_output(
    page: Page, plotly_app: ShinyAppProc
) -> None:
    page.goto(plotly_app.url)

    host = page.locator("#scatter")
    expect(host).to_be_visible()

    # Plotly attaches its rendered chart with the `js-plotly-plot` class on a
    # descendant of the host. If sizing is missing the chart is 0×0 and this
    # locator becomes invisible.
    expect(host.locator(".js-plotly-plot")).to_be_visible()

    # Direct-child assertion: no wrapper between the container and `#scatter`.
    expect(page.locator("[data-test=container] > #scatter")).to_be_attached()

    # Computed-style guard: the container CSS paints a hot-pink outline on
    # direct children only. A wrapper regression would strand the host at
    # the default outline.
    expect(host).to_have_css("outline-style", "solid")
    expect(host).to_have_css("outline-color", "rgb(255, 105, 180)")
