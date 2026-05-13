from __future__ import annotations

import pytest
import shiny.ui as sui
from shiny import reactive
from shinyui._input_slider import input_slider


def test_factory_returns_instance():
    s = input_slider("n", "N", 1, 100, 50)
    assert isinstance(s, input_slider)
    assert s.id == "n"


def test_tagify_matches_shiny_ui_input_slider():
    ours = input_slider("n", "N", 1, 100, 50).tagify()
    theirs = sui.input_slider("n", "N", 1, 100, 50)
    assert ours.get_html_string() == theirs.get_html_string()


def test_value_accessor_reads_input(mock_session):
    s = input_slider("n", "N", 1, 100, 50)
    mock_session.input.__getitem__.return_value = lambda: 25
    with reactive.isolate():
        assert s.value() == 25
    mock_session.input.__getitem__.assert_called_with("n")


def test_update_outside_session_raises():
    s = input_slider("n", "N", 1, 100, 50)  # no session
    match = r"input_slider\.update\(\) requires an active session"
    with pytest.raises(RuntimeError, match=match):
        s.update(value=42)


def test_update_uses_captured_session(mock_session):
    s = input_slider("n", "N", 1, 100, 50)
    s.update(value=42)
    mock_session.send_input_message.assert_called_once()
    name, payload = mock_session.send_input_message.call_args.args
    assert name == "n"
    assert payload["value"] == 42
