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

    # `<ShinyOutput>` does not add classes of its own; only the caller-supplied
    # ones should be present.
    expect(out).to_have_class(re.compile(r"\bcustom-a\b"))
    expect(out).to_have_class(re.compile(r"\bcustom-b\b"))

    # Arbitrary HTML attributes pass through to the rendered element.
    expect(out).to_have_attribute("data-test-marker", "x")

    # Direct-child assertion: `>` combinator fails if any wrapper sneaks in.
    expect(page.locator("[data-test=container] > #out")).to_be_attached()


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
