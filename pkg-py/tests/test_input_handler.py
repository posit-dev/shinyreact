import importlib
from typing import cast

import shinyreact  # noqa: F401  (import registers the handlers)
import shinyreact._input_handler
from shiny.input_handler import input_handlers
from shiny.module import ResolvedId
from shiny.session import Session

# Shiny hands every input handler `(value, name, session)`. Both shinyreact
# handlers ignore the last two, which is part of what these tests assert, so
# `None` stands in for them -- the casts say that is the point, not a missing
# fixture.
NO_NAME = cast(ResolvedId, None)
NO_SESSION = cast(Session, None)


def test_all_handlers_are_registered():
    assert "shinyreact.default" in input_handlers
    assert "shinyreact.asis" in input_handlers
    # The JS bundle pings `.shinyreact_init:shinyreact.init` every session;
    # without this registration the ping would raise on the Python server.
    # R's counterpart bootstraps dep discovery (test-dep-discovery.R).
    assert "shinyreact.init" in input_handlers


def test_default_handler_returns_value_unchanged():
    handler = input_handlers["shinyreact.default"]
    records = [{"name": "a", "size": 1}, {"name": "b", "size": 2}]
    assert handler(records, NO_NAME, NO_SESSION) == records
    assert handler([0, 100], NO_NAME, NO_SESSION) == [0, 100]
    assert handler(5, NO_NAME, NO_SESSION) == 5
    assert handler([], NO_NAME, NO_SESSION) == []
    assert handler(None, NO_NAME, NO_SESSION) is None


def test_asis_handler_returns_value_unchanged():
    handler = input_handlers["shinyreact.asis"]
    records = [{"name": "a"}, {"name": "b"}]
    assert handler(records, NO_NAME, NO_SESSION) == records
    assert handler([0, 100], NO_NAME, NO_SESSION) == [0, 100]
    assert handler(5, NO_NAME, NO_SESSION) == 5
    assert handler([], NO_NAME, NO_SESSION) == []
    assert handler(None, NO_NAME, NO_SESSION) is None


def test_default_handler_preserves_nested_structures():
    """Nesting survives, pinning the cross-language contract (#184).

    R's `default_input_handler()` has to actively avoid flattening these — the
    JSON the React component sent must come back the same shape from both
    servers. This test is the Python half of that contract.
    """
    handler = input_handlers["shinyreact.default"]
    assert handler([[1, 2], [3, 4]], NO_NAME, NO_SESSION) == [[1, 2], [3, 4]]
    assert handler([{"a": 1}, 5], NO_NAME, NO_SESSION) == [{"a": 1}, 5]
    # An empty array stays an empty array, not None.
    assert handler([], NO_NAME, NO_SESSION) == []


def test_reregistration_is_idempotent():
    # Re-running the module re-registers both handlers; force=True must not raise.
    importlib.reload(shinyreact._input_handler)
    assert "shinyreact.default" in input_handlers
    assert "shinyreact.asis" in input_handlers
