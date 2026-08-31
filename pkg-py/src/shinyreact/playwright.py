"""Websocket wire assertions for Playwright tests.

``WireTap`` gives tests access to the JSON payloads that actually crossed the
Shiny websocket — the contract between the server and the React client.
Playwright is a test-only dependency: importing this module (not the
``shinyreact`` package) requires it.

The R counterpart is ``shinyreact::wire_tap()``, with the same methods and
semantics.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, Callable

try:
    import playwright.sync_api  # noqa: F401  (presence check only)
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "shinyreact.playwright requires the `playwright` package, which is a "
        "test-only dependency. Install it with `pip install pytest-playwright` "
        "(or `pip install playwright`)."
    ) from e

if TYPE_CHECKING:
    from playwright.sync_api import Page, WebSocket

__all__ = ("WireTap",)

# An expectation matcher: a callable is satisfied by a truthy return; any
# other object is compared for equality.
Matcher = Callable[[Any], Any] | Any


class WireTap:
    """Passive tap on the Shiny websocket, with retrying expectations.

    Construct it before ``page.goto()`` — history is complete from
    construction onward::

        tap = WireTap(page)
        page.goto(app.url)
        tap.expect_input_value("bins", 30)
        tap.expect_output_value("dist_data", lambda d: d["breaks"][0] == 43.0)

    Cross-channel frame order (which output lands first, how outputs batch
    into a single ``values`` frame, busy/progress interleaving) is
    reactive-scheduling coincidence, not contract — so the tap deliberately
    does not expose a global frame stream. Within one channel (one output id,
    one message type, one input id) wire order is guaranteed, and the
    ``expect_*`` methods consume it through a cursor: each expectation scans
    the recorded history from just past the previous match, so values that
    arrive between checks are never missed — capture is lossless; polling
    only decides when to re-scan. Successive expectations on one channel
    therefore assert an ordered subsequence.
    """

    def __init__(self, page: Page) -> None:
        # Raw (direction, frame) stream. Cross-channel order in here is NOT a
        # contract; the per-channel methods below are the public surface.
        self._frames: list[tuple[str, dict[str, Any]]] = []
        # Per-channel scan cursors for the expect_* methods.
        self._cursors: dict[tuple[str, str], int] = {}
        self._page = page

        def on_websocket(ws: WebSocket) -> None:
            ws.on("framesent", lambda payload: self._add("send", payload))
            ws.on("framereceived", lambda payload: self._add("recv", payload))

        page.on("websocket", on_websocket)

    def _add(self, direction: str, payload: str | bytes) -> None:
        if isinstance(payload, bytes):
            return
        try:
            frame = json.loads(payload)
        except ValueError:
            return
        if isinstance(frame, dict):
            self._frames.append((direction, frame))

    # --- complete per-channel history (cursor-independent) -----------------

    def all_output_values(self, output_id: str) -> list[Any]:
        """Every value the server delivered for `output_id`, in order."""
        return [
            frame["values"][output_id]
            for direction, frame in self._frames
            if direction == "recv" and output_id in frame.get("values", {})
        ]

    def all_messages(self, message_id: str) -> list[Any]:
        """Every ``send_message()`` payload of `message_id`, in order."""
        out: list[Any] = []
        for direction, frame in self._frames:
            if direction != "recv":
                continue
            # Payload shape {id, data} per protocol/surface.json.
            msg = frame.get("custom", {}).get("shinyReactMessage")
            if msg and msg.get("id") == message_id:
                out.append(msg.get("data"))
        return out

    def all_input_values(self, input_id: str) -> list[Any]:
        """Every value the client sent for `input_id`, in order.

        Matches the bare id or any ``id:type`` wire id (e.g. the implicit
        ``:shinyreact.default`` suffix), so use the id you wrote in
        ``useShinyInput()``.
        """
        out: list[Any] = []
        for direction, frame in self._frames:
            if direction != "send":
                continue
            data = frame.get("data")
            if not isinstance(data, dict):
                continue
            for key, value in data.items():
                if key == input_id or key.startswith(input_id + ":"):
                    out.append(value)
        return out

    # --- retrying expectations (cursor-consuming) ---------------------------

    def expect_output_value(
        self, output_id: str, matcher: Matcher, timeout_s: float = 10
    ) -> Any:
        """Retrying expectation against the values delivered for `output_id`.

        A callable `matcher` is satisfied by a truthy return; any other
        object is compared for equality. Returns the matched value, or raises
        ``AssertionError`` at `timeout_s`. A matcher that raises on a value's
        shape counts as a non-match.
        """
        return self._expect(
            ("output", output_id),
            lambda: self.all_output_values(output_id),
            matcher,
            timeout_s,
        )

    def expect_message(
        self, message_id: str, matcher: Matcher, timeout_s: float = 10
    ) -> Any:
        """As :meth:`expect_output_value`, for ``send_message()`` payloads."""
        return self._expect(
            ("message", message_id),
            lambda: self.all_messages(message_id),
            matcher,
            timeout_s,
        )

    def expect_input_value(
        self, input_id: str, matcher: Matcher, timeout_s: float = 10
    ) -> Any:
        """As :meth:`expect_output_value`, for client-sent input values."""
        return self._expect(
            ("input", input_id),
            lambda: self.all_input_values(input_id),
            matcher,
            timeout_s,
        )

    def _expect(
        self,
        channel: tuple[str, str],
        values: Callable[[], list[Any]],
        matcher: Matcher,
        timeout_s: float,
    ) -> Any:
        matches: Callable[[Any], Any] = (
            matcher if callable(matcher) else lambda v: v == matcher
        )
        deadline = time.monotonic() + timeout_s
        last_exc: Exception | None = None
        while True:
            vals = values()
            start = self._cursors.get(channel, 0)
            for i in range(start, len(vals)):
                # A matcher that blows up on a value's shape (e.g. an early
                # `output: null` frame) is a non-match, not a test error; the
                # timeout message reports the last exception.
                try:
                    matched = matches(vals[i])
                except Exception as e:
                    matched = False
                    last_exc = e
                if matched:
                    # Consume through the match: the next expectation on this
                    # channel scans strictly-later values (ordered subsequence
                    # semantics). Non-matching values stay visible via the
                    # all_* views.
                    self._cursors[channel] = i + 1
                    return vals[i]
            if time.monotonic() >= deadline:
                raise AssertionError(
                    f"expect_{channel[0]}({channel[1]!r}): no matching value "
                    f"within {timeout_s}s; scanned {len(vals) - start} "
                    f"value(s) past the cursor: {vals[start:]!r}"
                    + (f"; last matcher error: {last_exc!r}" if last_exc else "")
                )
            self._page.wait_for_timeout(100)
