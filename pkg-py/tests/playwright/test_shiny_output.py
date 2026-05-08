import re

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

classname_app = create_app_fixture("apps/classname/app.py")


def test_custom_classname_lands_on_rendered_element(
    page: Page, classname_app: ShinyAppProc
) -> None:
    page.goto(classname_app.url)

    out = page.locator("#out")
    expect(out).to_be_visible()

    # `<ShinyOutput>` does not add classes of its own; only the caller-supplied
    # ones should be present.
    expect(out).to_have_class(re.compile(r"\bcustom-a\b"))
    expect(out).to_have_class(re.compile(r"\bcustom-b\b"))

    # Arbitrary HTML attributes pass through to the rendered element.
    expect(out).to_have_attribute("data-test-marker", "x")

    # Direct-child assertion: `>` combinator fails if any wrapper sneaks in.
    expect(page.locator("[data-test=container] > #out")).to_be_attached()
