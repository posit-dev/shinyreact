"""Tests for reactive_output (ui.tsx pattern: publishes JSON data, no placeholder)."""

from __future__ import annotations

import pytest
from shinyreact import reactive_output


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


def test_auto_output_ui_returns_none() -> None:
    @reactive_output
    def my_value():
        return {"x": 1}

    assert my_value.auto_output_ui() is None


def test_no_extra_deps_attribute() -> None:
    assert not hasattr(reactive_output, "extra_deps")
