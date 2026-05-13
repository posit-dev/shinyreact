from __future__ import annotations

import shiny.ui as sui
from htmltools import tags
from shinyui._accordion_panel import accordion_panel
from shinyui._children import AllowsChildren


def test_factory_returns_instance():
    p = accordion_panel("Settings", "body")
    assert isinstance(p, accordion_panel)
    assert isinstance(p, AllowsChildren)


def test_children_collected():
    p = accordion_panel("Settings", "a", "b")
    assert "a" in p.children and "b" in p.children


def test_tagify_matches_shiny():
    # accordion_panel() returns an AccordionPanel (not a plain Tag).
    # Compare key attributes that drive rendered output — random bslib panel IDs
    # make full HTML string comparison non-deterministic.
    ours = accordion_panel("Settings", "body").tagify()
    theirs = sui.accordion_panel("Settings", "body")
    assert ours._title == theirs._title
    assert ours._args == theirs._args
    assert ours._data_value == theirs._data_value
    assert ours._icon == theirs._icon


def test_with_block_appends():
    with accordion_panel("Settings") as p:
        p.append(tags.p("inside"))
    assert len(p.children) == 1
