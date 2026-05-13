"""Shared fixtures for shinyui tests.

Each test that needs `get_current_session()` to return something uses
the `mock_session` fixture, which yields a controllable Session-like object
and binds it as the current session for the duration of the test.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest
from shiny.session._utils import session_context


@pytest.fixture
def mock_session() -> Iterator[Any]:
    """Bind a MagicMock as the current session inside the test body."""
    session = MagicMock(name="MockSession")
    session.input = MagicMock(name="MockInput")
    # session_context calls namespace_context(session.ns), which requires a str
    session.ns = ""
    with session_context(session):
        yield session


@contextmanager
def no_session() -> Iterator[None]:
    """Helper: confirm no session is bound. Use for explicit clarity in tests."""
    from shiny.session import get_current_session
    assert get_current_session() is None, "Test expected no active session"
    yield
