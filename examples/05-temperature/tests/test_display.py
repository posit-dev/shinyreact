"""Pins the server echo — the half of this example the client does not compute.

The client converts locally and the server converts again; a threshold or
rounding change on one side without the other is a visible divergence, so both
sides need a test. `ui.test.ts` next to this file covers the client;
shiny's `local_server` fixture covers the server, in memory. Run it from the
app directory::

    pytest

The client rounds to whole degrees while the server keeps one decimal — the
`98.6` below is the server's answer for the same 37 °C the client shows as
`99°F`, which is exactly the divergence worth pinning.
"""

from __future__ import annotations

import pytest
from shiny.testserver import TestServerSession

# The app is a directory up from this `tests/` folder, so the `local_server`
# fixture (an already-started `test_server()` session) gets pointed at it.
pytestmark = pytest.mark.parametrize("local_server", ["../app.py"], indirect=True)


def test_display_wire_shape(local_server: TestServerSession) -> None:
    local_server.set_inputs(celsius=20)
    assert local_server.get_output("display") == {
        "celsius": 20,
        "fahrenheit": 68.0,
        "zone": "Comfortable",
    }


def test_fahrenheit_keeps_one_decimal(local_server: TestServerSession) -> None:
    local_server.set_inputs(celsius=37)
    assert local_server.get_output("display").value["fahrenheit"] == 98.6


@pytest.mark.parametrize(
    "celsius, zone",
    [
        (-40, "Freezing"),
        (0, "Freezing"),  # inclusive upper bound
        (1, "Cold"),
        (15, "Cold"),
        (16, "Comfortable"),
        (30, "Comfortable"),
        (31, "Hot"),
        (60, "Hot"),
    ],
)
def test_zone_thresholds(
    local_server: TestServerSession, celsius: int, zone: str
) -> None:
    local_server.set_inputs(celsius=celsius)
    assert local_server.get_output("display").value["zone"] == zone


def test_no_echo_before_the_clients_first_message(
    local_server: TestServerSession,
) -> None:
    # `input.celsius()` raises a silent exception while unset, so `display`
    # never renders at all — the `c is None` guard in `app.py` is unreachable
    # from a real client.
    assert local_server.get_output("display").status == "silent"
