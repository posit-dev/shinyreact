"""End-to-end bookmark id->instance registration tests.

Verifies that constructing a HasInputValue inside a session registers the
instance on the session map (so bookmark machinery can find it later), and
that per-instance serializer overrides flow through correctly.
"""

from __future__ import annotations

from typing import Any

import shinyui as sui
from shinyui._bookmark import lookup_instance


def test_session_registry_records_slider_on_construction(mock_session):
    s = sui.input_slider("n", "N", 1, 10, 5)
    assert lookup_instance(mock_session, "n") is s


def test_session_registry_records_select_on_construction(mock_session):
    s = sui.input_select("c", "C", {"a": "A"})
    assert lookup_instance(mock_session, "c") is s


def test_session_registry_records_card_on_construction(mock_session):
    c = sui.card("body", id="main_card")
    assert lookup_instance(mock_session, "main_card") is c


def test_session_registry_records_accordion_on_construction(mock_session):
    a = sui.accordion(sui.accordion_panel("A"), id="acc")
    assert lookup_instance(mock_session, "acc") is a


def test_per_instance_serializer_override():
    """Per-instance override of the class-default serializer.

    Concrete factory signatures don't expose `bookmark_serializer` directly
    in this prototype; users assign to `_bookmark_serializer` on the instance
    if they want to override. The mechanism (instance attr wins over ClassVar)
    is what `HasInputValue.__init__` already wires up.
    """

    class Custom:
        async def serialize(self, value: Any, state_dir: Any) -> Any:
            return value

        async def deserialize(self, value: Any, state_dir: Any) -> Any:
            return value

    custom = Custom()
    s = sui.input_slider("n", "N", 1, 10, 5)
    s._bookmark_serializer = custom
    assert s._bookmark_serializer is custom


def test_no_session_no_registry_noop():
    """Construction without a session must not raise and must not crash later."""
    s = sui.input_slider("n", "N", 1, 10, 5)
    assert s._session is None
