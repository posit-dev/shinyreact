from __future__ import annotations

import shinyuiclassonly as sui


def test_input_action_button_tagify_basic():
    b = sui.input_action_button("go", "Run")
    html = str(b.tagify())
    assert 'id="go"' in html
    assert "Run" in html


def test_input_action_button_stores_kwargs():
    b = sui.input_action_button("go", "Run", width="120px", disabled=True)
    assert b.id == "go"
    assert b.label == "Run"
    assert b.width == "120px"
    assert b.disabled is True


def test_input_action_button_has_no_value_or_update_methods():
    b = sui.input_action_button("go", "Run")
    assert not hasattr(b, "value")
    assert not hasattr(b, "update")


def test_input_action_button_does_not_register_input_handler():
    """shinyuiclassonly drops the __init_subclass__ handler registration.
    Importing input_action_button must NOT register
    ``shinyui.action`` (or any) into shiny's input_handlers registry."""
    from shiny.input_handler import input_handlers

    # Even if a parallel test of shinyui has already registered
    # 'shinyui.action', shinyuiclassonly itself must not add
    # 'shinyuiclassonly.action' or anything similar.
    registered = set(input_handlers.keys())
    # Importing shinyuiclassonly must not introduce its own handler keys.
    import shinyuiclassonly  # noqa: F401

    assert {k for k in input_handlers.keys() if "shinyuiclassonly" in k} == set()
    # Sanity: registered set is at least as large as before (no removals).
    assert registered.issubset(input_handlers.keys())


def test_input_action_button_is_uiinput():
    b = sui.input_action_button("go", "Run")
    assert isinstance(b, sui.UiInput)
