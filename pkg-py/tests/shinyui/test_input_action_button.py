from __future__ import annotations

import pytest
import shiny.ui as sui
from shiny import reactive
from shinyui._input_action_button import UiInputActionButton, input_action_button


def test_factory_returns_instance():
    b = input_action_button("go", "Go")
    assert isinstance(b, UiInputActionButton)
    assert b.id == "go"


def test_tagify_matches_shiny_ui_input_action_button():
    ours = input_action_button("go", "Go").tagify()
    theirs = sui.input_action_button("go", "Go")
    assert ours.get_html_string() == theirs.get_html_string()


def test_clicked_zero_when_input_is_none(mock_session):
    b = input_action_button("go", "Go")
    mock_session.input.__getitem__.return_value = lambda: None
    with reactive.isolate():
        assert b.clicked() == 0


def test_clicked_returns_int_value(mock_session):
    b = input_action_button("go", "Go")
    mock_session.input.__getitem__.return_value = lambda: 3
    with reactive.isolate():
        assert b.clicked() == 3
    mock_session.input.__getitem__.assert_called_with("go")


def test_update_outside_session_raises():
    b = input_action_button("go", "Go")
    with pytest.raises(RuntimeError, match=r"requires an active session"):
        b.update(label="New")


def test_update_sends_input_message(mock_session):
    b = input_action_button("go", "Go")
    b.update(label="New", disabled=True)
    # `shiny.ui.update_action_button` runs label through session._process_ui
    # which yields a MagicMock under the mock; we only assert send happened
    # with the right id and the plain-bool `disabled` flag passed through.
    mock_session.send_input_message.assert_called_once()
    name, payload = mock_session.send_input_message.call_args.args
    assert name == "go"
    assert payload["disabled"] is True
    assert "label" in payload  # processed by shiny; exact value not pinned here
