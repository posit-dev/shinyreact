"""Pins the echo output and the bookmark effect's inputs.

`shiny.testserver.test_server()` loads this app through `ReactApp`, so the
server half of the example runs in memory. The *restore* half does not: it is a
property of the rendered page and the browser URL, and stays pinned by
`pkg-py/tests/test_bookmark_restore.py` and its Playwright counterpart. Run it
from the app directory::

    pytest
"""

from __future__ import annotations

from pathlib import Path

from shiny.testserver import test_server

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_greeting_wire_shape() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(txt="hi", num=5, chk=True)
        # `checked` is the string "yes"/"no", and `txt` is repr'd, so quoted.
        assert ts.get_output("greeting") == "text='hi' num=5 checked=yes"

        ts.set_inputs(chk=False)
        assert ts.get_output("greeting") == "text='hi' num=5 checked=no"


def test_greeting_renders_from_the_hook_defaults() -> None:
    # The client renders immediately rather than gating on
    # `useShinyInitialized()`, so the first values the server sees are the
    # hook defaults (or the restored ones).
    with test_server(APP) as ts:
        ts.set_inputs(txt="", num=0, chk=False)
        assert ts.get_output("greeting") == "text='' num=0 checked=no"


def test_a_bookmark_click_is_an_event_input() -> None:
    # `bookmark_clicks` is write-only and `priority: "event"`, with the count
    # incremented per click; `ignore_init=True` means the mount-time 0 does
    # not bookmark. The URL rewrite itself needs a browser — see the
    # Playwright suite — so all this asserts is that the effect runs cleanly.
    with test_server(APP) as ts:
        ts.set_inputs(txt="hi", num=5, chk=True)
        ts.set_inputs(bookmark_clicks=0)
        ts.set_inputs(bookmark_clicks=1)

        assert ts.to_values().is_ok
        assert ts.get_output("greeting") == "text='hi' num=5 checked=yes"
