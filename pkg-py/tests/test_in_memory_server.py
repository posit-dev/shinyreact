"""Server-side behavior of the ui.tsx pattern, driven in memory.

Shiny's `local_server` pytest fixture (py-shiny#2470) is an already-started
`test_server()` session: it runs an app's server function against a mock
connection — inputs in, output values out, no browser and no subprocess. That
suits shinyreact particularly well — a ui.tsx server is *only* reactive
computation, so what a test wants to assert is the JSON that reaches
`useShinyOutputValue()`, which is exactly what `get_output()` hands back.

The fixture defaults to `app.py` beside the test file; the apps here are the
Playwright fixture apps, reused as-is, so each test points the fixture at one
with an indirect parametrization. These tests pin the server half of claims
whose client half still needs a browser (see `pkg-py/tests/playwright/`). The
fixture needs no `tests-e2e` extras, so this file lives in the unit suite.

Two shinyreact-specific notes for anyone adding to this file:

- **Untyped input ids need no `:shinyreact.default` suffix.** The React hook
  appends it on the wire, but both Python handlers are no-ops, so
  `set_inputs(n=1)` and `set_inputs(**{"n:shinyreact.default": 1})` reach the
  server identically. Use the suffixed form only when the handler itself is
  what you are testing (see `test_input_handler_dispatch.py`).
- **Event inputs need two calls.** A client registers a `useShinyInput`
  default at mount and sends the event after, so an output guarded by
  `@reactive.event(..., ignore_init=True)` only fires on the *second*
  `set_inputs` for that id.
"""

from __future__ import annotations

import pytest
from shiny.testserver import TestServerSession

MODULE_COUNTER = pytest.mark.parametrize(
    "local_server", ["playwright/apps/module_counter/app.py"], indirect=True
)
OUTPUT_ERROR = pytest.mark.parametrize(
    "local_server", ["playwright/apps/output-error/app.py"], indirect=True
)


@MODULE_COUNTER
def test_reactive_output_publishes_raw_json(local_server: TestServerSession) -> None:
    """The value a `reactive_output` returns reaches the client unwrapped.

    `test_reactive_output.py` asserts this through `Renderer.transform()`;
    here it goes through a real session, so nothing between the render function
    and the wire can re-wrap it.
    """
    local_server.set_inputs(**{"a-count": 3})
    assert local_server.get_output("a-serverCount") == 3


@MODULE_COUNTER
def test_module_namespaces_stay_isolated(local_server: TestServerSession) -> None:
    """In-memory twin of `playwright/test_module_namespaces.py`.

    A scope is the test-side counterpart of the `SessionProxy` a module server
    receives, so the module's ids can be read bare.
    """
    a = local_server.make_scope("a")
    a.set_inputs(count=2)
    assert a.get_output("serverCount") == 2

    # Namespace isolation: counter "b" is untouched, and its output has not
    # rendered at all.
    assert local_server.get_output("b-serverCount").status == "silent"
    assert local_server.get_output("a-serverCount") == 2


@OUTPUT_ERROR
def test_output_error_statuses(local_server: TestServerSession) -> None:
    """Server half of `playwright/test_output_error.py`.

    Which of the three outcomes an input produces — a value, a silent
    `req()`, or an error message — is decided server-side; only the rendering
    of each needs the browser.
    """
    local_server.set_inputs(n=1)
    assert local_server.get_output("answer") == "ok: 1"
    assert local_server.get_output("answer").status == "ok"

    # A silent req() failure blanks the output: `status` describes the *latest*
    # render, so it reports "silent" with no value rather than the stale
    # "ok: 1" — matching the blank the browser shows (asserted in the e2e test).
    local_server.set_inputs(n=-1)
    assert local_server.get_output("answer").status == "silent"

    local_server.set_inputs(n=0)
    assert local_server.get_output("answer").status == "error"
    assert local_server.get_output("answer").error == "invalid number of 'breaks'"

    # Recovering clears the error.
    local_server.set_inputs(n=2)
    assert local_server.get_output("answer") == "ok: 2"
    assert local_server.get_output("answer").error is None
