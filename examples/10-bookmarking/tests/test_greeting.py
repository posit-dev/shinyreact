"""Pins the echo output and the bookmark effect's inputs.

Shiny's `local_server` fixture loads this app through `ReactApp`, so the
server half of the example runs in memory. The *restore* half does not: it is a
property of the rendered page and the browser URL, and stays pinned by
`pkg-py/tests/test_bookmark_restore.py` and its Playwright counterpart. Run it
from the app directory::

    pytest
"""

from __future__ import annotations

import pytest
from shiny.testserver import TestServerSession

# The app is a directory up from this `tests/` folder, so the `local_server`
# fixture (an already-started `test_server()` session) gets pointed at it.
pytestmark = pytest.mark.parametrize("local_server", ["../app.py"], indirect=True)


def test_greeting_wire_shape(local_server: TestServerSession) -> None:
    local_server.set_inputs(txt="hi", num=5, chk=True)
    # `checked` is the string "yes"/"no", and `txt` is repr'd, so quoted.
    assert local_server.get_output("greeting") == "text='hi' num=5 checked=yes"

    local_server.set_inputs(chk=False)
    assert local_server.get_output("greeting") == "text='hi' num=5 checked=no"


def test_greeting_renders_from_the_hook_defaults(
    local_server: TestServerSession,
) -> None:
    # The client renders immediately rather than gating on
    # `useShinyInitialized()`, so the first values the server sees are the
    # hook defaults (or the restored ones).
    local_server.set_inputs(txt="", num=0, chk=False)
    assert local_server.get_output("greeting") == "text='' num=0 checked=no"


def test_a_bookmark_click_is_an_event_input(local_server: TestServerSession) -> None:
    # `bookmark_clicks` is write-only and `priority: "event"`, with the count
    # incremented per click; `ignore_init=True` means the mount-time 0 does
    # not bookmark. The URL rewrite itself needs a browser — see the
    # Playwright suite — so all this asserts is that the effect runs cleanly.
    local_server.set_inputs(txt="hi", num=5, chk=True)
    local_server.set_inputs(bookmark_clicks=0)
    local_server.set_inputs(bookmark_clicks=1)

    assert local_server.to_values().is_ok
    assert local_server.get_output("greeting") == "text='hi' num=5 checked=yes"
