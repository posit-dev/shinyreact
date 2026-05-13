from __future__ import annotations

import pytest
import shinyui as sui
from shiny import reactive


@pytest.mark.parametrize(
    "maker,accessor,suffix,value",
    [
        (lambda: sui.input_slider("n", "N", 1, 10, 5), "value", "", 7),
        (lambda: sui.input_select("c", "C", {"a": "A"}), "value", "", "a"),
        (lambda: sui.card("b", id="m"), "full_screen_value", "", True),
        (
            lambda: sui.accordion(sui.accordion_panel("A"), id="acc"),
            "open_panels",
            "",
            ["A"],
        ),
        (
            lambda: sui.output_plot("p", click=True),
            "click_value",
            "_click",
            {"x": 1, "y": 2},
        ),
        (
            lambda: sui.output_plot("p", brush=True),
            "brush_value",
            "_brush",
            {"xmin": 1},
        ),
    ],
)
def test_accessor_reads_correct_id(mock_session, maker, accessor, suffix, value):
    inst = maker()
    expected_id = f"{inst.id}{suffix}"
    mock_session.input.__getitem__.return_value = lambda: value
    with reactive.isolate():
        result = getattr(inst, accessor)()
    if isinstance(value, list):
        assert result == tuple(value)
    else:
        assert result == value
    mock_session.input.__getitem__.assert_called_with(expected_id)


@pytest.mark.parametrize(
    "maker,accessor",
    [
        (lambda: sui.input_slider("n", "N", 1, 10, 5), "value"),
        (lambda: sui.card("b", id="m"), "full_screen_value"),
        (lambda: sui.output_plot("p", click=True), "click_value"),
    ],
)
def test_accessor_raises_outside_session(maker, accessor):
    inst = maker()
    with pytest.raises(RuntimeError, match=r"requires an active session"):
        with reactive.isolate():
            getattr(inst, accessor)()
