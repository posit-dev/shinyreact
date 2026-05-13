"""Pin the prototype's handler-registration state.

Most shinyui classes do NOT declare a custom input handler — shiny's
built-in bindings handle the wire format. The one exception is
UiInputActionButton, which carries a "shinyui.action" handler purely
to demonstrate the __init_subclass__ auto-registration pattern (see
the module docstring on _input_action_button.py for the trade-off).
"""

from __future__ import annotations

import pytest
import shinyui as sui


@pytest.mark.parametrize(
    "cls",
    [
        sui.UiInputSlider,
        sui.UiInputSelect,
        sui.UiCard,
        sui.UiAccordion,
    ],
)
def test_class_declares_no_custom_handler(cls):
    """These classes use shiny's default wire handling for input values."""
    assert cls.input_handler_name == ""
    assert cls._input_handler is None


def test_action_button_declares_custom_handler():
    """UiInputActionButton ships a 'shinyui.action' handler via __init_subclass__."""
    assert sui.UiInputActionButton.input_handler_name == "shinyui.action"
    assert sui.UiInputActionButton._input_handler is not None
