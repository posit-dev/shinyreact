import unittest.mock
from unittest.mock import AsyncMock

import pytest
from shinyjson import send_json


class TestSendJson:
    @pytest.mark.asyncio
    async def test_sends_correct_message_format(self):
        """send_json sends the expected format to send_custom_message."""
        session = AsyncMock()
        await send_json(session, "logEvent", {"text": "hello"})

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"type": "logEvent", "data": {"text": "hello"}},
        )

    @pytest.mark.asyncio
    async def test_sends_string_data(self):
        """send_json works with string data."""
        session = AsyncMock()
        await send_json(session, "notify", "simple string")

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"type": "notify", "data": "simple string"},
        )

    @pytest.mark.asyncio
    async def test_sends_list_data(self):
        """send_json works with list data."""
        session = AsyncMock()
        await send_json(session, "update", [1, 2, 3])

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"type": "update", "data": [1, 2, 3]},
        )

    @pytest.mark.asyncio
    async def test_namespaces_type_with_resolve_id(self):
        """send_json uses resolve_id to namespace the message type."""
        session = AsyncMock()

        # Simulate being inside a Shiny module with namespace "mymod"
        with unittest.mock.patch(
            "shinyjson._send_json.resolve_id",
            side_effect=lambda x: f"mymod-{x}",
        ):
            await send_json(session, "logEvent", {"text": "hello"})

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"type": "mymod-logEvent", "data": {"text": "hello"}},
        )
