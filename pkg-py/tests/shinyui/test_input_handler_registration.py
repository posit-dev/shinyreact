"""Pin the prototype's handler-registration state.

UPDATED FROM PLAN: UiAccordion does NOT register a custom input handler in this
prototype — shiny's accordion binding sends a plain JSON list that doesn't need
server-side wire coercion. open_panels() coerces list->tuple at read time.
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
    """All prototype classes use shiny's default wire handling for input values."""
    assert cls.input_handler_name == ""
    assert cls._input_handler is None
