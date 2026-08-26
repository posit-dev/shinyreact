"""Tests for shinyreact.send_message (renamed from post_message / send_json)."""

from __future__ import annotations

import unittest.mock
from unittest.mock import AsyncMock

import pytest
from shinyreact import send_message


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_sends_correct_message_format(self):
        """send_message sends the expected format to send_custom_message."""
        session = AsyncMock()
        await send_message(session, "logEvent", {"text": "hello"})

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"id": "logEvent", "data": {"text": "hello"}},
        )

    @pytest.mark.asyncio
    async def test_sends_string_data(self):
        """send_message works with string data."""
        session = AsyncMock()
        await send_message(session, "notify", "simple string")

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"id": "notify", "data": "simple string"},
        )

    @pytest.mark.asyncio
    async def test_sends_list_data(self):
        """send_message works with list data."""
        session = AsyncMock()
        await send_message(session, "update", [1, 2, 3])

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"id": "update", "data": [1, 2, 3]},
        )

    @pytest.mark.asyncio
    async def test_namespaces_id_with_resolve_id(self):
        """send_message uses resolve_id to namespace the message id."""
        session = AsyncMock()

        # Simulate being inside a Shiny module with namespace "mymod"
        with unittest.mock.patch(
            "shinyreact._send_message.resolve_id",
            side_effect=lambda x: f"mymod-{x}",
        ):
            await send_message(session, "logEvent", {"text": "hello"})

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"id": "mymod-logEvent", "data": {"text": "hello"}},
        )
