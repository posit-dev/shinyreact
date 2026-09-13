"""Two silent failure modes of the hosted-widget recipe in `shiny-outputs.md`.

Neither is a shinyreact bug — both are Shiny's own behavior — but the
`@render.ui` holder recipe leads straight into them, so the skill documents
them and these tests pin the claims for Python. (R was verified separately;
R has no e2e suite yet, see issue #194.)
"""

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

timing_app = create_app_fixture("apps/hosted_input_timing/app.py")


def test_update_before_the_holder_renders_is_dropped(
    page: Page, timing_app: ShinyAppProc
) -> None:
    page.goto(timing_app.url)

    # The app fired `update_slider("late_bins", value=30)` in its first flush,
    # before this holder had rendered. The widget arrives at its own initial
    # value; the update was dropped with no error and no warning.
    page.locator("#show").click()
    expect(page.locator("#late_widget .irs-single")).to_have_text("9")

    # Control, so the assertion above cannot pass vacuously: the identical
    # call, once the widget really exists, does land.
    page.locator("#bump").click()
    expect(page.locator("#late_widget .irs-single")).to_have_text("30")


def test_hosted_widget_hidden_on_first_paint_never_renders(
    page: Page, timing_app: ShinyAppProc
) -> None:
    page.goto(timing_app.url)

    # Both holders sit in a `display: none` panel. `suspend_when_hidden=False`
    # is the only difference between them, and it is the difference between a
    # widget and an empty div.
    expect(page.locator("#unsuspended_bins")).to_be_attached()
    expect(page.locator("#suspended_bins")).to_have_count(0)
