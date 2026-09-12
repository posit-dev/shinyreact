"""Pins both outputs, including the traditional `@render.data_frame` one.

Shiny's `local_server` fixture reads a `reactive_output` and a traditional
renderer the same way, so the payload `ShinyOutput` hands to
`shiny-data-frame` can be asserted in memory. Run it from the app directory::

    pytest
"""

from __future__ import annotations

import pytest
from shiny.testserver import TestServerSession

# The app is a directory up from this `tests/` folder, so the `local_server`
# fixture (an already-started `test_server()` session) gets pointed at it.
pytestmark = pytest.mark.parametrize("local_server", ["../app.py"], indirect=True)


def test_greeting_counts_the_rows(local_server: TestServerSession) -> None:
    local_server.set_inputs(row_count=3)
    assert local_server.get_output("greeting") == "Showing 3 rows"


def test_data_frame_payload(local_server: TestServerSession) -> None:
    local_server.set_inputs(row_count=3)
    payload = local_server.get_output("my_table").value["payload"]

    assert payload["columns"] == ["Name", "Value", "Category"]
    assert payload["data"] == [
        ["Item 1", 10, "B"],
        ["Item 2", 20, "A"],
        ["Item 3", 30, "B"],
    ]


def test_row_count_drives_both_outputs(local_server: TestServerSession) -> None:
    local_server.set_inputs(row_count=5)
    assert local_server.get_output("greeting") == "Showing 5 rows"
    assert len(local_server.get_output("my_table").value["payload"]["data"]) == 5
