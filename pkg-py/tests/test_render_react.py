"""Tests for the render_react renderer (app.py pattern: walks UI -> JSON spec)."""

from __future__ import annotations

import pytest
from htmltools import HTMLDependency, TagList, tags
from shinyreact import Node, render_react


@pytest.mark.asyncio
async def test_node_is_walked_to_wire_tree() -> None:
    node = Node(type="Card", props={"title": "Hi"})

    @render_react
    def out():
        return node

    assert await out.transform(node) == {
        "type": "react",
        "name": "Card",
        "props": {"title": "Hi"},
        "children": [],
    }


@pytest.mark.asyncio
async def test_child_string_becomes_text_node() -> None:
    node = Node(type="Card", props={}, children=["hi"])

    @render_react
    def out():
        return node

    transformed = await out.transform(node)
    assert transformed["children"] == [{"type": "text", "value": "hi"}]


@pytest.mark.asyncio
async def test_tag_is_walked() -> None:
    @render_react
    def out():
        return tags.div("x", class_="c")

    assert await out.transform(tags.div("x", class_="c")) == {
        "type": "tag",
        "name": "div",
        "props": {"className": "c"},
        "children": [{"type": "text", "value": "x"}],
    }


@pytest.mark.asyncio
async def test_taglist_single_child_unwraps_through_transform() -> None:
    tl = TagList(tags.div("x"))

    @render_react
    def out():
        return tl

    assert await out.transform(tl) == {
        "type": "tag",
        "name": "div",
        "props": {},
        "children": [{"type": "text", "value": "x"}],
    }


@pytest.mark.asyncio
async def test_taglist_multi_child_returns_list_through_transform() -> None:
    tl = TagList(tags.div("a"), tags.span("b"))

    @render_react
    def out():
        return tl

    result = await out.transform(tl)
    assert isinstance(result, list)
    assert [n["name"] for n in result] == ["div", "span"]


@pytest.mark.asyncio
async def test_render_time_dep_emits_warning() -> None:
    dep = HTMLDependency(name="d", version="1.0", source={"subdir": "/tmp"})
    node = Node(type="Card", props={}, children=[dep])

    @render_react
    def out():
        return node

    with pytest.warns(UserWarning, match="HTMLDependency"):
        await out.transform(node)


def test_auto_output_ui_returns_output_react() -> None:
    @render_react
    def my_card():
        return Node(type="Card", props={})

    rendered = str(my_card.auto_output_ui())
    assert "shinyreact-output" in rendered
    assert 'id="my_card"' in rendered
