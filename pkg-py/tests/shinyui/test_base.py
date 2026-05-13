from __future__ import annotations

import pytest
from shinyui._base import UiComponent


class _Dummy(UiComponent):
    """Minimal concrete subclass for testing."""

    def tagify(self):
        from htmltools import tags

        return tags.div("dummy")


def test_uicomponent_is_abstract():
    with pytest.raises(TypeError):
        UiComponent()  # type: ignore[abstract]


def test_session_captured_as_none_without_session():
    c = _Dummy()
    assert c._session is None


def test_session_captured_when_present(mock_session):
    c = _Dummy()
    assert c._session is mock_session


def test_require_session_raises_when_none():
    c = _Dummy()
    with pytest.raises(
        RuntimeError, match=r"_Dummy\.foo\(\) requires an active session"
    ):
        c._require_session(for_op="foo")


def test_require_session_returns_captured(mock_session):
    c = _Dummy()
    assert c._require_session(for_op="foo") is mock_session


def test_require_session_falls_back_to_current(mock_session):
    """If _session is None at init but a session is active at call time, use it."""
    from shiny.session._utils import session_context

    c = _Dummy()
    c._session = None
    with session_context(mock_session):
        assert c._require_session(for_op="foo") is mock_session


def test_enter_raises_with_class_name():
    c = _Dummy()
    with pytest.raises(TypeError, match=r"_Dummy does not accept children"):
        c.__enter__()


def test_read_input_uses_current_session_and_id(mock_session):
    c = _Dummy()
    c.id = "my_id"  # type: ignore[attr-defined]
    mock_session.input.__getitem__.return_value = lambda: 42
    assert c._read_input() == 42
    mock_session.input.__getitem__.assert_called_with("my_id")


def test_read_input_suffix(mock_session):
    c = _Dummy()
    c.id = "p"  # type: ignore[attr-defined]
    mock_session.input.__getitem__.return_value = lambda: {"x": 1}
    assert c._read_input("_click") == {"x": 1}
    mock_session.input.__getitem__.assert_called_with("p_click")
