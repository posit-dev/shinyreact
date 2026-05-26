from __future__ import annotations

import sys

import pytest

import shinyuiclassonly as sui


def test_accordion_tagify_with_panels():
    a = sui.accordion(
        sui.accordion_panel("A", "body a"),
        sui.accordion_panel("B", "body b"),
        id="acc",
    )
    rendered = a.tagify()
    html = str(rendered)
    assert "acc" in html


def test_accordion_with_block_collects_panels():
    import sys

    with sui.accordion(id="acc") as a:
        sys.displayhook(sui.accordion_panel("Settings", "x"))
    assert len(a.children) == 1
    assert isinstance(a.children[0], sui.accordion_panel)


def test_accordion_has_no_open_panels_or_update_methods():
    a = sui.accordion(sui.accordion_panel("A"), id="acc")
    assert not hasattr(a, "open_panels")
    assert not hasattr(a, "update")


def test_accordion_id_required_for_input_routing():
    """The id is still useful (shiny's accordion binding uses it). The
    spec leaves it required to match shinyui."""
    # accordion still constructs without explicit id — it just won't have
    # a server-readable input wire. We allow id to be None to match the
    # spec's "id optional on layouts" intent for shinyuiclassonly.
    sui.accordion(sui.accordion_panel("A"))  # must not raise


def test_accordion_tagify_inline_rebuilds_panels():
    """accordion.tagify() rebuilds shiny.ui.accordion_panel wrappers from
    each child's stored state (because shiny.ui.accordion does an
    isinstance(panel, AccordionPanel) check). Same quirk as shinyui."""
    a = sui.accordion(
        sui.accordion_panel("A", "body"),
        id="acc",
        open="A",
    )
    html = str(a.tagify())
    assert "body" in html


def test_init_rejects_non_panel_positional_arg():
    """Core form: bare string positional arg raises TypeError at construction."""
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        sui.accordion("some text", id="acc")  # type: ignore[arg-type]


def test_append_rejects_non_panel():
    """Direct .append() of a non-panel child raises TypeError."""
    a = sui.accordion(id="acc")
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        a.append("text")  # type: ignore[arg-type]


def test_express_with_block_rejects_bare_string():
    """Express form: bare string inside `with accordion(...)` raises TypeError.

    This validates the displayhook -> dispatch_to_active_parent -> append
    path that is the real-world hazard described in #106.
    """
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        with sui.accordion(id="acc"):
            sys.displayhook("Some descriptive text")


def test_tagify_rejects_directly_mutated_children():
    """Defense-in-depth: bypassing __init__/append still fails at tagify()."""
    a = sui.accordion(sui.accordion_panel("A"), id="acc")
    a.children.append("text")  # bypass the guards
    with pytest.raises(TypeError, match="accordion children must be accordion_panel"):
        a.tagify()


def test_error_message_names_offending_type():
    """The TypeError includes the offending child's type name."""
    a = sui.accordion(id="acc")
    with pytest.raises(TypeError, match=r"got str\b"):
        a.append("text")  # type: ignore[arg-type]


def test_well_formed_accordion_still_tagifies():
    """Regression guard: validation does not break the happy path."""
    a = sui.accordion(
        sui.accordion_panel("A", "body-a"),
        sui.accordion_panel("B", "body-b"),
        id="acc",
    )
    tag = a.tagify()
    assert tag.attrs.get("id") == "acc"
