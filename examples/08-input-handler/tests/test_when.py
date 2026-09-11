"""Pins the input handler's coercion at the server, in memory.

This example exists to show that `useShinyInput(..., {type: "shiny.datetime"})`
makes the server read a `datetime`. `shiny.testserver.test_server()` can assert
exactly that, because `set_inputs` takes the **wire** id — so the `:type`
suffix the hook appends is part of the test, and the handler really runs. Run
it from the app directory::

    pytest
"""

from __future__ import annotations

from pathlib import Path

from shiny.testserver import test_server

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_the_handler_turns_unix_seconds_into_a_datetime() -> None:
    with test_server(APP) as ts:
        # What the client sends: unix *seconds*, under the suffixed wire id.
        ts.set_inputs(**{"when:shiny.datetime": 1756382400})
        echoed = ts.get_output("when_info").value

        # Shiny's handler decodes as UTC and strips the tzinfo, so the value
        # is the same on every machine: 1756382400 is 2025-08-28T12:00:00Z.
        assert echoed == "datetime → datetime.datetime(2025, 8, 28, 12, 0)"


def test_an_unsuffixed_value_is_not_coerced() -> None:
    # The suffix is what buys the coercion: without it the number arrives as a
    # number. This is the failure mode the per-id type contract exists to
    # prevent, and the reason to write the suffix out in the test above.
    with test_server(APP) as ts:
        ts.set_inputs(when=1756382400)
        assert ts.get_output("when_info") == "int → 1756382400"


def test_nothing_renders_before_the_clients_first_message() -> None:
    # `input.when()` raises a silent exception while unset, so the `None`
    # branch in `app.py` (the em dash) is unreachable from a real client.
    with test_server(APP) as ts:
        assert ts.get_output("when_info").status == "silent"
