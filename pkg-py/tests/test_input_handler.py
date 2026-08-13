import importlib

import shinyreact  # noqa: F401  (import registers the handlers)
import shinyreact._input_handler
from shiny.input_handler import input_handlers


def test_both_handlers_are_registered():
    assert "shinyreact.default" in input_handlers
    assert "shinyreact.asis" in input_handlers


def test_default_handler_returns_value_unchanged():
    handler = input_handlers["shinyreact.default"]
    records = [{"name": "a", "size": 1}, {"name": "b", "size": 2}]
    assert handler(records, None, None) == records
    assert handler([0, 100], None, None) == [0, 100]
    assert handler(5, None, None) == 5
    assert handler([], None, None) == []
    assert handler(None, None, None) is None


def test_asis_handler_returns_value_unchanged():
    handler = input_handlers["shinyreact.asis"]
    records = [{"name": "a"}, {"name": "b"}]
    assert handler(records, None, None) == records
    assert handler([0, 100], None, None) == [0, 100]
    assert handler(5, None, None) == 5
    assert handler([], None, None) == []
    assert handler(None, None, None) is None


def test_default_handler_preserves_nested_structures():
    """Nesting survives, pinning the cross-language contract (#184).

    R's `default_input_handler()` has to actively avoid flattening these — the
    JSON the React component sent must come back the same shape from both
    servers. This test is the Python half of that contract.
    """
    handler = input_handlers["shinyreact.default"]
    assert handler([[1, 2], [3, 4]], None, None) == [[1, 2], [3, 4]]
    assert handler([{"a": 1}, 5], None, None) == [{"a": 1}, 5]
    # An empty array stays an empty array, not None.
    assert handler([], None, None) == []


def test_reregistration_is_idempotent():
    # Re-running the module re-registers both handlers; force=True must not raise.
    importlib.reload(shinyreact._input_handler)
    assert "shinyreact.default" in input_handlers
    assert "shinyreact.asis" in input_handlers
