from __future__ import annotations

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


def test_tagify_returns_tag():
    # accordion_panel.tagify() now returns a rendered Tag (chained .tagify()
    # on shiny's AccordionPanel wrapper). The class stamps a placeholder
    # _accordion_id so standalone rendering works outside a parent accordion.
    from htmltools import Tag

    ours = accordion_panel("Settings", "body").tagify()
    assert isinstance(ours, Tag)
    # Sanity: rendered HTML contains the panel title and body content.
    html = ours.get_html_string()
    assert "Settings" in html
    assert "body" in html


def test_with_block_appends():
    with accordion_panel("Settings") as p:
        p.append(tags.p("inside"))
    assert len(p.children) == 1
