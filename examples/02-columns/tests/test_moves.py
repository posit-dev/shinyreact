"""Pins the server's move handling as the client drives it.

`shiny.testserver.test_server()` runs `app.py`'s server against a mock
connection, so the `move_item` → `column_data` round trip can be asserted
without a browser. Run it from the app directory::

    pytest

`move_item` is an **event** input (`@reactive.event(..., ignore_init=True)`),
so a test has to mirror what the client does: `useShinyInput("move_item",
null)` registers the `null` default at mount, and the drop sends the move
after. With a single `set_inputs` the move *is* the init and is ignored.
"""

from __future__ import annotations

from pathlib import Path

from shiny.testserver import test_server

APP = Path(__file__).resolve().parents[1] / "app.py"

INITIAL = {
    "A": ["Apple", "Apricot"],
    "B": ["Banana", "Blueberry"],
    "C": ["Cherry", "Cranberry"],
}


def test_column_data_starts_at_the_initial_three_columns() -> None:
    with test_server(APP) as ts:
        assert ts.get_output("column_data") == INITIAL


def test_a_move_removes_from_the_source_and_appends_to_the_target() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(move_item=None)  # the hook's default, sent at mount
        ts.set_inputs(move_item={"item": "Apple", "from": "A", "to": "C"})

        assert ts.get_output("column_data") == {
            "A": ["Apricot"],
            "B": ["Banana", "Blueberry"],
            # Appended, not inserted in sorted position.
            "C": ["Cherry", "Cranberry", "Apple"],
        }


def test_a_move_of_an_item_the_source_does_not_hold_is_ignored() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(move_item=None)
        ts.set_inputs(move_item={"item": "Cherry", "from": "A", "to": "B"})
        assert ts.get_output("column_data") == INITIAL


def test_moves_accumulate() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(move_item=None)
        ts.set_inputs(move_item={"item": "Apple", "from": "A", "to": "B"})
        ts.set_inputs(move_item={"item": "Apple", "from": "B", "to": "C"})

        data = ts.get_output("column_data").value
        assert data["A"] == ["Apricot"]
        assert data["B"] == ["Banana", "Blueberry"]
        assert data["C"] == ["Cherry", "Cranberry", "Apple"]
