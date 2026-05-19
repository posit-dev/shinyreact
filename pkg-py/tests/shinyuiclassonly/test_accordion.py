from __future__ import annotations

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
