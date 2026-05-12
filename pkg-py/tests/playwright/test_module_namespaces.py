from playwright.sync_api import Locator, Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

module_counter_app = create_app_fixture("apps/module_counter/app.py")


def _counter(page: Page, namespace: str) -> Locator:
    return page.locator(f".counter[data-test-namespace={namespace}]")


def test_module_counter_namespacing(
    page: Page, module_counter_app: ShinyAppProc
) -> None:
    page.goto(module_counter_app.url)

    a = _counter(page, "a")
    b = _counter(page, "b")

    expect(a.locator(".value")).to_have_text("0")
    expect(b.locator(".value")).to_have_text("0")

    a.locator("button.increment").click()
    a.locator("button.increment").click()

    # Counter "a" round-tripped through the namespaced reactive_output.
    expect(a.locator(".value")).to_have_text("2")

    # Namespace isolation: counter "b" must be untouched.
    expect(b.locator(".value")).to_have_text("0")
