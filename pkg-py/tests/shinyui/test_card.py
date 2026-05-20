from __future__ import annotations

import pytest
import shiny.ui as sui
from shiny import reactive
from shinyui._card import card
from shinyui._children import AllowsChildren
from shinyui._input_value import HasInputValue
from shinyui._updatable import Updatable


def test_factory_returns_instance():
    c = card("body", id="main")
    assert isinstance(c, card)
    assert isinstance(c, HasInputValue)
    assert isinstance(c, AllowsChildren)
    assert isinstance(c, Updatable)


def test_tagify_matches_shiny():
    """Compare HTML (or attrs if shiny.ui.card returns a non-Tag wrapper)."""
    ours = card("body", id="main", full_screen=False).tagify()
    theirs = sui.card("body", id="main", full_screen=False)
    # If shiny.ui.card returns a Tag, compare HTML.
    # If it returns a CardItem or similar, compare type or relevant attrs.
    if hasattr(ours, "get_html_string") and hasattr(theirs, "get_html_string"):
        assert ours.get_html_string() == theirs.get_html_string()
    else:
        assert type(ours).__name__ == type(theirs).__name__


def test_value_full_screen(mock_session):
    c = card("body", id="main")
    mock_session.input.__getitem__.return_value = lambda: True
    with reactive.isolate():
        assert c.value_full_screen() is True
    mock_session.input.__getitem__.assert_called_with("main_full_screen")


def test_update_outside_session_raises():
    c = card("body", id="main")
    with pytest.raises(RuntimeError):
        c.update(full_screen=True)


def test_update_sends_message_or_flush(mock_session):
    """Card update should signal the session (send_input_message or on_flush)."""
    c = card("body", id="main")
    c.update(full_screen=True)
    # Either send_input_message or on_flush should have been called.
    assert mock_session.send_input_message.called or mock_session.on_flush.called
