from __future__ import annotations

import sys

import pytest
from shiny import reactive
from shinyui._accordion import accordion
from shinyui._accordion_panel import accordion_panel
from shinyui._children import AllowsChildren
from shinyui._input_value import HasInputValue
from shinyui._updatable import Updatable


def test_factory_returns_instance():
    a = accordion(accordion_panel("A"), accordion_panel("B"), id="acc")
    assert isinstance(a, accordion)
    assert isinstance(a, HasInputValue)
    assert isinstance(a, AllowsChildren)
    assert isinstance(a, Updatable)


def test_tagify_attribute_parity():
    """Compare key attrs vs shiny.ui.accordion; random bslib ids break full HTML eq."""
    import shiny.ui as sui

    ours = accordion(
        accordion_panel("A", "body-a"),
        accordion_panel("B", "body-b"),
        id="acc",
        open="A",
    ).tagify()
    theirs = sui.accordion(
        sui.accordion_panel("A", "body-a"),
        sui.accordion_panel("B", "body-b"),
        id="acc",
        open="A",
    ).tagify()
    # Both resolve to a TagifiedTag (<div>); assert same type and id attribute.
    assert type(ours).__name__ == type(theirs).__name__
    assert ours.attrs.get("id") == theirs.attrs.get("id")


def test_children_collected():
    a = accordion(accordion_panel("A"), accordion_panel("B"), id="acc")
    assert len(a.children) == 2


def test_open_panels_accessor(mock_session):
    a = accordion(accordion_panel("A"), id="acc")
    mock_session.input.__getitem__.return_value = lambda: ["A"]
    with reactive.isolate():
        assert a.open_panels() == ("A",)


def test_open_panels_empty_returns_empty_tuple(mock_session):
    a = accordion(accordion_panel("A"), id="acc")
    mock_session.input.__getitem__.return_value = lambda: []
    with reactive.isolate():
        assert a.open_panels() == ()


def test_open_panels_none_returns_empty_tuple(mock_session):
    a = accordion(accordion_panel("A"), id="acc")
    mock_session.input.__getitem__.return_value = lambda: None
    with reactive.isolate():
        assert a.open_panels() == ()


def test_update_outside_session_raises():
    a = accordion(accordion_panel("A"), id="acc")
    with pytest.raises(RuntimeError):
        a.update(open=("A",))


def test_update_sends_message(mock_session):
    a = accordion(accordion_panel("A"), accordion_panel("B"), id="acc")
    a.update(open=("A", "B"))
    # shiny's update_accordion defers via session.on_flush() rather than calling
    # send_input_message directly.  Assert that a flush callback was registered.
    mock_session.on_flush.assert_called_once()


def test_init_rejects_non_panel_positional_arg():
    """Core form: bare string positional arg raises TypeError at construction."""
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        accordion("some text", id="acc")  # type: ignore[arg-type]


def test_append_rejects_non_panel():
    """Direct .append() of a non-panel child raises TypeError."""
    a = accordion(id="acc")
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        a.append("text")  # type: ignore[arg-type]


def test_express_with_block_rejects_bare_string():
    """Express form: bare string inside `with accordion(...)` raises TypeError.

    This validates the displayhook -> dispatch_to_active_parent -> append
    path that is the real-world hazard described in #106.
    """
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        with accordion(id="acc"):
            sys.displayhook("Some descriptive text")


def test_tagify_rejects_directly_mutated_children():
    """Defense-in-depth: bypassing __init__/append still fails at tagify()."""
    a = accordion(accordion_panel("A"), id="acc")
    a.children.append("text")  # bypass the guards
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        a.tagify()


def test_error_message_names_offending_type():
    """The TypeError includes the offending child's type name."""
    a = accordion(id="acc")
    with pytest.raises(TypeError, match=r"got str\b"):
        a.append("text")  # type: ignore[arg-type]


def test_well_formed_accordion_still_tagifies():
    """Regression guard: validation does not break the happy path."""
    a = accordion(
        accordion_panel("A", "body-a"),
        accordion_panel("B", "body-b"),
        id="acc",
    )
    tag = a.tagify()
    assert tag.attrs.get("id") == "acc"
