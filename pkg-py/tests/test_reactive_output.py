"""Tests for the reactive_output decorator with the tree wire format."""

from __future__ import annotations

import pytest
from htmltools import HTMLDependency, TagList, tags
from shinyreact import Node, reactive_output


@pytest.mark.asyncio
async def test_passthrough_dict() -> None:
    @reactive_output
    def out():
        return {"a": 1, "b": [2, 3]}

    assert await out.transform({"a": 1, "b": [2, 3]}) == {"a": 1, "b": [2, 3]}


@pytest.mark.asyncio
async def test_passthrough_primitive() -> None:
    @reactive_output
    def out():
        return 42

    assert await out.transform(42) == 42


@pytest.mark.asyncio
async def test_passthrough_string_is_json_not_text_node() -> None:
    @reactive_output
    def out():
        return "hello"

    # Top-level str is JSON passthrough, NOT a {"type": "text"} node.
    assert await out.transform("hello") == "hello"


@pytest.mark.asyncio
async def test_passthrough_list() -> None:
    @reactive_output
    def out():
        return [1, 2, 3]

    assert await out.transform([1, 2, 3]) == [1, 2, 3]


@pytest.mark.asyncio
async def test_passthrough_none() -> None:
    @reactive_output
    def out():
        return None

    assert await out.transform(None) is None


@pytest.mark.asyncio
async def test_node_is_walked_to_wire_tree() -> None:
    node = Node(type="Card", props={"title": "Hi"})

    @reactive_output
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

    @reactive_output
    def out():
        return node

    transformed = await out.transform(node)
    assert transformed["children"] == [{"type": "text", "value": "hi"}]


@pytest.mark.asyncio
async def test_tag_is_walked() -> None:
    @reactive_output
    def out():
        return tags.div("x", class_="c")

    assert await out.transform(tags.div("x", class_="c")) == {
        "type": "tag",
        "name": "div",
        "props": {"className": "c"},
        "children": [{"type": "text", "value": "x"}],
    }


@pytest.mark.asyncio
async def test_render_time_dep_emits_warning() -> None:
    dep = HTMLDependency(name="d", version="1.0", source={"subdir": "/tmp"})
    node = Node(type="Card", props={}, children=[dep])

    @reactive_output
    def out():
        return node

    with pytest.warns(UserWarning, match="HTMLDependency"):
        await out.transform(node)


def test_auto_output_ui_returns_ui_output() -> None:
    @reactive_output
    def my_card():
        return {"x": 1}

    rendered = str(my_card.auto_output_ui())
    assert "shinyreact-output" in rendered
    assert 'id="my_card"' in rendered


def test_no_extra_deps_attribute() -> None:
    assert not hasattr(reactive_output, "extra_deps")


@pytest.mark.asyncio
async def test_taglist_single_child_unwraps_through_transform() -> None:
    tl = TagList(tags.div("x"))

    @reactive_output
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

    @reactive_output
    def out():
        return tl

    result = await out.transform(tl)
    assert isinstance(result, list)
    assert [n["name"] for n in result] == ["div", "span"]
