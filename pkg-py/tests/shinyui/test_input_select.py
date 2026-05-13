from __future__ import annotations

import pytest
import shiny.ui as sui
from shiny import reactive
from shinyui._input_select import UiInputSelect, input_select


def test_factory_returns_instance():
    s = input_select("col", "Column", {"a": "A", "b": "B"})
    assert isinstance(s, UiInputSelect)


def test_tagify_matches_shiny_ui_input_select():
    ours = input_select("col", "Column", {"a": "A", "b": "B"}).tagify()
    theirs = sui.input_select("col", "Column", {"a": "A", "b": "B"})
    assert ours.get_html_string() == theirs.get_html_string()


def test_value_accessor(mock_session):
    s = input_select("col", "Column", {"a": "A"})
    mock_session.input.__getitem__.return_value = lambda: "a"
    with reactive.isolate():
        assert s.value() == "a"


def test_update_outside_session_raises():
    s = input_select("col", "Column", {"a": "A"})
    with pytest.raises(RuntimeError):
        s.update(selected="a")


def test_update_sends_message(mock_session):
    s = input_select("col", "Column", {"a": "A"})
    s.update(selected="a")
    mock_session.send_input_message.assert_called_once()
    name, payload = mock_session.send_input_message.call_args.args
    assert name == "col"
    # shiny.ui.update_select wraps a single str in a list before sending
    assert payload["value"] == ["a"]
