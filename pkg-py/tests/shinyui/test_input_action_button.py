from __future__ import annotations

import pytest
import shiny.ui as sui
from shiny import reactive
from shiny.input_handler import input_handlers
from shinyui._input_action_button import input_action_button


def test_factory_returns_instance():
    b = input_action_button("go", "Go")
    assert isinstance(b, input_action_button)
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


def test_input_handler_auto_registered_via_init_subclass():
    """The class is registered under 'shinyui.action' at class-definition
    time via the _InputHandlerAutoRegister mixin's __init_subclass__ hook.
    """
    assert input_action_button.input_handler_name == "shinyui.action"
    # `input_handlers` is dict-like.
    assert "shinyui.action" in input_handlers


def test_input_handler_coerces_to_int():
    h = input_action_button._input_handler
    assert h(None, None, None) == 0
    assert h(3, None, None) == 3
    assert h("5", None, None) == 5


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
