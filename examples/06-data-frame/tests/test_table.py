"""Pins both outputs, including the traditional `@render.data_frame` one.

`shiny.testserver.test_server()` reads a `reactive_output` and a traditional
renderer the same way, so the payload `ShinyOutput` hands to
`shiny-data-frame` can be asserted in memory. Run it from the app directory::

    pytest
"""

from __future__ import annotations

from pathlib import Path

from shiny.testserver import test_server

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_greeting_counts_the_rows() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(row_count=3)
        assert ts.get_output("greeting") == "Showing 3 rows"


def test_data_frame_payload() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(row_count=3)
        payload = ts.get_output("my_table").value["payload"]

        assert payload["columns"] == ["Name", "Value", "Category"]
        assert payload["data"] == [
            ["Item 1", 10, "B"],
            ["Item 2", 20, "A"],
            ["Item 3", 30, "B"],
        ]


def test_row_count_drives_both_outputs() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(row_count=5)
        assert ts.get_output("greeting") == "Showing 5 rows"
        assert len(ts.get_output("my_table").value["payload"]["data"]) == 5
