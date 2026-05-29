from __future__ import annotations

from typing import Any

from htmltools import tags
from shinyui._base import UiComponent
from shinyui._bookmark import lookup_instance
from shinyui._input_value import HasInputValue


class _Pinger(UiComponent, HasInputValue):
    input_handler_name = "test.ping"

    @staticmethod
    def _input_handler(value: Any, name: Any, session: Any) -> Any:
        return ("pinged", value)

    def tagify(self):
        return tags.div(id=self.id)


class _Plain(UiComponent, HasInputValue):
    """No input_handler — defaults to None."""

    def tagify(self):
        return tags.div(id=self.id)


def test_id_is_stored():
    p = _Plain(id="x")
    assert p.id == "x"


def test_no_session_no_registration():
    """Module-level construction: no session, no registry."""
    _Plain(id="x")  # should not raise


def test_session_registers_self(mock_session):
    p = _Plain(id="x")
    assert lookup_instance(mock_session, "x") is p


def test_register_input_handler_classmethod(monkeypatch):
    captured = {}

    def fake_register(name, fn):
        captured[name] = fn

    monkeypatch.setattr("shinyui._input_value.register_input_handler", fake_register)
    _Pinger._register_input_handler()
    assert captured == {"test.ping": _Pinger._input_handler}


def test_register_input_handler_noop_when_no_handler(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        "shinyui._input_value.register_input_handler",
        lambda n, f: captured.update({n: f}),
    )
    _Plain._register_input_handler()
    assert captured == {}


def test_class_level_bookmark_serializer_inherited():
    class S:
        async def serialize(self, value, state_dir):  # noqa: D401
            return value

        async def deserialize(self, value, state_dir):
            return value

    class _Custom(UiComponent, HasInputValue):
        bookmark_serializer = S()

        def tagify(self):
            return tags.div(id=self.id)

    c = _Custom(id="x")
    assert c._bookmark_serializer is _Custom.bookmark_serializer


def test_per_instance_bookmark_serializer_overrides_class():
    class S:
        async def serialize(self, value, state_dir):
            return value

        async def deserialize(self, value, state_dir):
            return value

    class _Custom(UiComponent, HasInputValue):
        bookmark_serializer = S()

        def tagify(self):
            return tags.div(id=self.id)

    inst_ser = S()
    c = _Custom(id="x", bookmark_serializer=inst_ser)
    assert c._bookmark_serializer is inst_ser
