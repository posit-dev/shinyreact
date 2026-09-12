"""Pins the server's move handling as the client drives it.

Shiny's `local_server` fixture runs `app.py`'s server against a mock
connection, so the `move_item` → `column_data` round trip can be asserted
without a browser. Run it from the app directory::

    pytest

`move_item` is an **event** input (`@reactive.event(..., ignore_init=True)`),
so a test has to mirror what the client does: `useShinyInput("move_item",
null)` registers the `null` default at mount, and the drop sends the move
after. With a single `set_inputs` the move *is* the init and is ignored.
"""

from __future__ import annotations

import pytest
from shiny.testserver import TestServerSession

# The app is a directory up from this `tests/` folder, so the `local_server`
# fixture (an already-started `test_server()` session) gets pointed at it.
pytestmark = pytest.mark.parametrize("local_server", ["../app.py"], indirect=True)

INITIAL = {
    "A": ["Apple", "Apricot"],
    "B": ["Banana", "Blueberry"],
    "C": ["Cherry", "Cranberry"],
}


def test_column_data_starts_at_the_initial_three_columns(
    local_server: TestServerSession,
) -> None:
    assert local_server.get_output("column_data") == INITIAL


def test_a_move_removes_from_the_source_and_appends_to_the_target(
    local_server: TestServerSession,
) -> None:
    local_server.set_inputs(move_item=None)  # the hook's default, sent at mount
    local_server.set_inputs(move_item={"item": "Apple", "from": "A", "to": "C"})

    assert local_server.get_output("column_data") == {
        "A": ["Apricot"],
        "B": ["Banana", "Blueberry"],
        # Appended, not inserted in sorted position.
        "C": ["Cherry", "Cranberry", "Apple"],
    }


def test_a_move_of_an_item_the_source_does_not_hold_is_ignored(
    local_server: TestServerSession,
) -> None:
    local_server.set_inputs(move_item=None)
    local_server.set_inputs(move_item={"item": "Cherry", "from": "A", "to": "B"})
    assert local_server.get_output("column_data") == INITIAL


def test_moves_accumulate(local_server: TestServerSession) -> None:
    local_server.set_inputs(move_item=None)
    local_server.set_inputs(move_item={"item": "Apple", "from": "A", "to": "B"})
    local_server.set_inputs(move_item={"item": "Apple", "from": "B", "to": "C"})

    data = local_server.get_output("column_data").value
    assert data["A"] == ["Apricot"]
    assert data["B"] == ["Banana", "Blueberry"]
    assert data["C"] == ["Cherry", "Cranberry", "Apple"]
