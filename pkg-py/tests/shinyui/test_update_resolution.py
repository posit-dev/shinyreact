from __future__ import annotations

import inspect

import pytest
import shinyui as sui


@pytest.mark.parametrize(
    "maker",
    [
        lambda: sui.input_slider("n", "N", 1, 10, 5),
        lambda: sui.input_select("c", "C", {"a": "A"}),
        lambda: sui.card("b", id="m"),
        lambda: sui.accordion(sui.accordion_panel("A"), id="acc"),
    ],
)
def test_update_raises_outside_session(maker):
    inst = maker()
    with pytest.raises(RuntimeError, match=r"requires an active session"):
        inst.update()


def test_update_uses_captured_session(mock_session):
    s = sui.input_slider("n", "N", 1, 10, 5)
    s.update(value=7)
    mock_session.send_input_message.assert_called_once()


def test_update_no_session_kwarg():
    """update() must not accept a `session=` kwarg."""
    s = sui.input_slider("n", "N", 1, 10, 5)
    sig = inspect.signature(s.update)
    assert "session" not in sig.parameters
