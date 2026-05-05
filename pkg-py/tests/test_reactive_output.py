"""Tests for the unified reactive_output decorator.

Covers all behaviors that previously lived in shinyjson.render_json (passthrough)
and shinyjsonold.render (Spec/Node flattening + auto_output_ui).
"""
from __future__ import annotations

import pytest

from shinyreact import Element, Node, Spec, reactive_output


@pytest.mark.asyncio
async def test_passthrough_dict() -> None:
    """Plain dicts pass through unchanged for useShinyOutput consumption."""

    @reactive_output
    def out():
        return {"a": 1, "b": [2, 3]}

    transformed = await out.transform({"a": 1, "b": [2, 3]})
    assert transformed == {"a": 1, "b": [2, 3]}


@pytest.mark.asyncio
async def test_passthrough_primitive() -> None:
    @reactive_output
    def out():
        return 42

    assert await out.transform(42) == 42


@pytest.mark.asyncio
async def test_spec_flattened() -> None:
    """Spec values are flattened via Spec.to_dict()."""
    spec = Spec(
        root="r",
        elements={"r": Element(type="Card", props={"title": "Hi"})},
    )

    @reactive_output
    def out():
        return spec

    assert await out.transform(spec) == spec.to_dict()


@pytest.mark.asyncio
async def test_node_flattened() -> None:
    """Node values are flattened via Node.to_spec().to_dict()."""
    node = Node(type="Card", props={"title": "Hi"})

    @reactive_output
    def out():
        return node

    assert await out.transform(node) == node.to_spec().to_dict()


def test_auto_output_ui_returns_ui_output() -> None:
    """Express mode auto-generates a shinyreact-output container."""

    @reactive_output
    def my_card():
        return {"x": 1}

    tag = my_card.auto_output_ui()
    rendered = str(tag)
    assert "shinyreact-output" in rendered
    assert 'id="my_card"' in rendered


def test_no_extra_deps_attribute() -> None:
    """The unified decorator drops the extra_deps extension hook."""
    assert not hasattr(reactive_output, "extra_deps")


@pytest.mark.asyncio
async def test_passthrough_string() -> None:
    @reactive_output
    def out():
        return "hello"

    assert await out.transform("hello") == "hello"


@pytest.mark.asyncio
async def test_passthrough_none() -> None:
    @reactive_output
    def out():
        return None

    assert await out.transform(None) is None


@pytest.mark.asyncio
async def test_passthrough_list() -> None:
    @reactive_output
    def out():
        return [1, 2, 3]

    assert await out.transform([1, 2, 3]) == [1, 2, 3]
