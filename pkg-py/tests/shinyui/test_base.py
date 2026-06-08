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


def test_require_session_falls_back_to_root_of_current(mock_session):
    """If _session is None at init but a session is active at call time, use
    the root scope of that current session. shinyui component ids are
    un-namespaced, so the fallback explicitly steps up to ``.root_scope()``
    even if the current session is a module-namespaced scope. See the
    Core/Express unification comment in ``UiComponent._require_session``.
    """
    from shiny.session._utils import session_context

    # Pin .root_scope() to a sentinel so we can verify the explicit step-up.
    mock_session.root_scope.return_value = mock_session

    c = _Dummy()
    c._session = None
    with session_context(mock_session):
        assert c._require_session(for_op="foo") is mock_session
    mock_session.root_scope.assert_called()


def test_uicomponent_does_not_support_context_manager_protocol():
    """UiComponent subclasses that don't inherit AllowsChildren must not be
    usable as context managers. The check is now static (pyright catches
    `with input_slider(...):` because input_slider has no __enter__); at
    runtime Python raises TypeError with its standard protocol message.
    """
    c = _Dummy()
    with pytest.raises(TypeError, match=r"context manager protocol"):
        with c:  # noqa: B017  intentional protocol-violation check
            pass


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
