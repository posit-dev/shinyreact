"""Unit tests for shinyreact.playwright.WireTap (fake page, no browser).

Mirrors pkg-r/tests/testthat/test-wire-tap.R — the two taps present the same
methods and semantics, so their unit suites assert the same behaviors on the
same frames. The real-browser coverage is
pkg-py/tests/playwright/test_wire_frames.py.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from shinyreact.playwright import WireTap


class FakePage:
    """Just enough Page for WireTap: event registration and a no-op clock."""

    def on(self, event: str, handler: Any) -> None:
        pass

    def wait_for_timeout(self, ms: float) -> None:
        pass


def make_tap(frames: list[tuple[str, dict[str, Any]]]) -> WireTap:
    tap = WireTap(FakePage())  # type: ignore[arg-type]
    for direction, frame in frames:
        tap._add(direction, json.dumps(frame))
    return tap


def test_all_output_values_in_order_per_output():
    tap = make_tap(
        [
            ("recv", {"values": {"a": 1, "b": "x"}}),
            ("recv", {"values": {"a": 2}}),
            ("send", {"data": {"a": 99}}),  # wrong direction: ignored
        ]
    )
    assert tap.all_output_values("a") == [1, 2]
    assert tap.all_output_values("b") == ["x"]
    assert tap.all_output_values("missing") == []


def test_all_input_values_matches_bare_and_typed_wire_ids():
    tap = make_tap(
        [
            ("send", {"method": "update", "data": {"bins:shinyreact.default": 30}}),
            ("send", {"method": "update", "data": {"bins": 5}}),
            ("send", {"method": "update", "data": {"binsight": 1}}),  # not a match
            ("recv", {"values": {"bins": 7}}),  # wrong direction: ignored
        ]
    )
    assert tap.all_input_values("bins") == [30, 5]


def test_all_messages_filters_by_type():
    tap = make_tap(
        [
            ("recv", {"custom": {"shinyReactMessage": {"id": "notify", "data": 1}}}),
            ("recv", {"custom": {"shinyReactMessage": {"id": "other", "data": 2}}}),
            ("recv", {"custom": {"shinyReactMessage": {"id": "notify", "data": 3}}}),
        ]
    )
    assert tap.all_messages("notify") == [1, 3]
    assert tap.all_messages("nope") == []


def test_expect_matches_object_by_equality_and_fn_by_truthiness():
    tap = make_tap(
        [
            ("recv", {"values": {"a": {"n": 1}}}),
            ("recv", {"values": {"a": {"n": 2}}}),
        ]
    )
    assert tap.expect_output_value("a", {"n": 1}, timeout_s=0) == {"n": 1}
    assert tap.expect_output_value("a", lambda v: v["n"] == 2, timeout_s=0) == {"n": 2}


def test_expect_cursor_consumes_an_ordered_subsequence():
    tap = make_tap(
        [
            ("send", {"data": {"bins": 30}}),
            ("send", {"data": {"bins": 5}}),
            ("send", {"data": {"bins": 30}}),
        ]
    )
    tap.expect_input_value("bins", 30, timeout_s=0)
    tap.expect_input_value("bins", 5, timeout_s=0)
    # The second 30 is strictly later than the 5 the cursor sits on.
    tap.expect_input_value("bins", 30, timeout_s=0)
    # Nothing is left past the cursor.
    with pytest.raises(AssertionError, match="scanned 0 value"):
        tap.expect_input_value("bins", 30, timeout_s=0)


def test_matcher_exception_is_a_nonmatch_and_reported_on_timeout():
    # The first value is None (the early `output: null` frame); a shape-blind
    # matcher raises on it and must still reach the real value.
    tap = make_tap(
        [
            ("recv", {"values": {"a": None}}),
            ("recv", {"values": {"a": {"n": 1}}}),
        ]
    )
    assert tap.expect_output_value("a", lambda v: v["n"] == 1, timeout_s=0) == {"n": 1}

    tap2 = make_tap([("recv", {"values": {"a": None}})])
    with pytest.raises(AssertionError, match="last matcher error"):
        tap2.expect_output_value("a", lambda v: v["n"] == 1, timeout_s=0)


def test_non_json_and_binary_payloads_are_ignored():
    tap = WireTap(FakePage())  # type: ignore[arg-type]
    tap._add("recv", "not json")
    tap._add("recv", b"\x00\x01")
    tap._add("recv", json.dumps([1, 2, 3]))  # non-dict frame
    assert tap.all_output_values("a") == []
