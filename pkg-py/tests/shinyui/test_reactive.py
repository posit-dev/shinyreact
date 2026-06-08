from __future__ import annotations

from shiny import reactive
from shinyui._reactive import reactive_calc_method


class _Counter:
    """Tests caching: the wrapped method is invoked once per change."""

    def __init__(self) -> None:
        self.calls = 0

    @reactive_calc_method
    def value(self) -> int:
        self.calls += 1
        return 42


def test_method_returns_value_under_reactive_isolate():
    c = _Counter()
    with reactive.isolate():
        assert c.value() == 42


def test_cached_per_instance():
    """Two different instances should have independent caches."""
    a = _Counter()
    b = _Counter()
    with reactive.isolate():
        assert a.value() == 42
        assert b.value() == 42
    assert a.calls == 1
    assert b.calls == 1
