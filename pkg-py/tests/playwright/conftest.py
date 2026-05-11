"""Pytest fixtures for the shinyreact Playwright e2e suite.

The `shiny.pytest` plugin auto-registers `local_app` and `create_app_fixture`,
so this file mainly exists to bridge `pytest-playwright`'s `connect_options`
fixture to the env vars exported by the `setup-playwright-remote` GitHub
Action — when CI runs the browser inside a Docker container, those vars tell
us to call `browser_type.connect()` instead of `browser_type.launch()`.

Locally, the env vars are unset and `connect_options` returns `None`, which
makes pytest-playwright fall back to the default launch path.

Pattern lifted from py-shiny:
https://github.com/posit-dev/py-shiny/blob/c446400bb87c18fd8dccac8202965ca1a2774cd7/tests/playwright/conftest.py
"""

from __future__ import annotations

import os
from inspect import signature

import pytest
from playwright.sync_api import BrowserType


@pytest.fixture(scope="session")
def connect_options() -> dict[str, str] | None:
    ws_endpoint = os.getenv("PW_TEST_CONNECT_WS_ENDPOINT")
    if not ws_endpoint:
        return None

    # Some playwright versions name the kwarg `endpoint`, others `ws_endpoint`.
    endpoint_arg = (
        "endpoint"
        if "endpoint" in signature(BrowserType.connect).parameters
        else "ws_endpoint"
    )
    options: dict[str, str] = {endpoint_arg: ws_endpoint}

    expose_network = os.getenv("PW_TEST_CONNECT_EXPOSE_NETWORK")
    if expose_network:
        options["expose_network"] = expose_network

    return options
