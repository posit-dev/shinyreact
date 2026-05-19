"""Assert __all__ matches what we export and the dropped symbols stay dropped."""

from __future__ import annotations

import shinyuiclassonly as sui

EXPECTED = {
    "AllowsChildren",
    "CtxTag",
    "UiComponent",
    "UiInput",
    "UiLayout",
    "UiOutput",
    "accordion",
    "accordion_panel",
    "card",
    "input_action_button",
    "input_select",
    "input_slider",
    "output_code",
    "output_plot",
    "render_plot",
}


def test_all_matches_expected():
    assert set(sui.__all__) == EXPECTED


def test_each_name_is_actually_exported():
    for name in sui.__all__:
        assert hasattr(sui, name), f"{name} listed in __all__ but not exported"


def test_dropped_shinyui_symbols_are_not_exported():
    """Symbols intentionally dropped from shinyuiclassonly relative to shinyui."""
    for name in ("HasInputValue", "Updatable", "lookup_component"):
        assert not hasattr(sui, name), f"{name} should not exist on shinyuiclassonly"
