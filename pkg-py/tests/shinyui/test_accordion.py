from __future__ import annotations

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
    )
    # Both resolve to a Tag (<div>); assert same type and id attribute.
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
