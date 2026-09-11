"""Server-side behavior of the ui.tsx pattern, driven in memory.

`shiny.testserver.test_server()` (py-shiny#2470) runs an app's server function
against a mock connection: inputs in, output values out, no browser and no
subprocess. That suits shinyreact particularly well — a ui.tsx server is *only*
reactive computation, so what a test wants to assert is the JSON that reaches
`useShinyOutputValue()`, which is exactly what `get_output()` hands back.

The apps here are the Playwright fixture apps, reused as-is: these tests pin
the server half of claims whose client half still needs a browser (see
`pkg-py/tests/playwright/`). `test_server` needs no `tests-e2e` extras, so this
file lives in the unit suite.

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

from pathlib import Path

from shiny.testserver import test_server

APPS = Path(__file__).parent / "playwright" / "apps"


def test_reactive_output_publishes_raw_json() -> None:
    """The value a `reactive_output` returns reaches the client unwrapped.

    `test_reactive_output.py` asserts this through `Renderer.transform()`;
    here it goes through a real session, so nothing between the render function
    and the wire can re-wrap it.
    """
    with test_server(APPS / "module_counter" / "app.py") as ts:
        ts.set_inputs(**{"a-count": 3})
        assert ts.get_output("a-serverCount") == 3


def test_module_namespaces_stay_isolated() -> None:
    """In-memory twin of `playwright/test_module_namespaces.py`.

    A scope is the test-side counterpart of the `SessionProxy` a module server
    receives, so the module's ids can be read bare.
    """
    with test_server(APPS / "module_counter" / "app.py") as ts:
        with ts.make_scope("a") as a:
            a.set_inputs(count=2)
            assert a.get_output("serverCount") == 2

        # Namespace isolation: counter "b" is untouched, and its output has not
        # rendered at all.
        assert ts.get_output("b-serverCount").status == "silent"
        assert ts.get_output("a-serverCount") == 2


def test_output_error_statuses() -> None:
    """Server half of `playwright/test_output_error.py`.

    Which of the three outcomes an input produces — a value, a silent
    `req()`, or an error message — is decided server-side; only the rendering
    of each needs the browser.
    """
    with test_server(APPS / "output-error" / "app.py") as ts:
        ts.set_inputs(n=1)
        assert ts.get_output("answer") == "ok: 1"
        assert ts.get_output("answer").status == "ok"

        # A *silent* req() failure is invisible in memory: real Shiny sends a
        # null value that blanks the output (asserted in the e2e test), but
        # `test_server` leaves the previous value recorded, so `status` stays
        # "ok" with the stale "ok: 1". "silent" means "never rendered", not
        # "rendered nothing this time" — don't assert silence here.
        ts.set_inputs(n=-1)
        assert ts.get_output("answer") == "ok: 1"

        ts.set_inputs(n=0)
        assert ts.get_output("answer").status == "error"
        assert ts.get_output("answer").error == "invalid number of 'breaks'"

        # Recovering clears the error.
        ts.set_inputs(n=2)
        assert ts.get_output("answer") == "ok: 2"
        assert ts.get_output("answer").error is None
