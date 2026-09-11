"""Pins this example's server outputs as the client sees them.

`test_faithful.py` next to this file tests the binner as a pure function;
this file drives the *app* — `shiny.testserver.test_server()` runs the server
against a mock connection, so `dist_data` and `dist_caption` can be asserted
exactly as they arrive at `useShinyOutputValue()`. No browser, no subprocess.

Both Python servers are covered, because `app.py` (Express) and `app-core.py`
(Core) are claimed to be interchangeable over one `www/` client.

Run it from the app directory, the way a user of the app would::

    pytest

An input id needs no `:shinyreact.default` suffix here: the React hook appends
it on the wire, but Python's handler is a no-op, so `set_inputs(bins=9)`
reaches the server identically.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from shiny.testserver import test_server

EXAMPLE = Path(__file__).resolve().parents[1]
APPS = [EXAMPLE / "app.py", EXAMPLE / "app-core.py"]

# Mirrored in test_faithful.py, tests/test-histogram.R and tests/ui.test.ts.
COUNTS_9 = [16, 37, 30, 16, 14, 57, 67, 29, 6]


@pytest.mark.parametrize("app", APPS, ids=lambda p: p.name)
def test_dist_data_wire_shape(app: Path) -> None:
    with test_server(app) as ts:
        ts.set_inputs(bins=9)
        data = ts.get_output("dist_data").value
        assert list(data) == ["breaks", "counts"]
        assert data["counts"] == COUNTS_9
        assert data["breaks"][0] == 43.0
        assert data["breaks"][-1] == pytest.approx(96.0)


@pytest.mark.parametrize("app", APPS, ids=lambda p: p.name)
def test_dist_caption_pluralizes(app: Path) -> None:
    with test_server(app) as ts:
        ts.set_inputs(bins=9)
        assert ts.get_output("dist_caption") == "272 eruptions in 9 bins"

        ts.set_inputs(bins=1)
        assert ts.get_output("dist_caption") == "272 eruptions in 1 bin"
        assert ts.get_output("dist_data").value["counts"] == [272]


@pytest.mark.parametrize("app", APPS, ids=lambda p: p.name)
def test_neither_output_renders_before_the_first_bins_message(app: Path) -> None:
    # `input.bins()` raises a silent exception while unset, so both outputs
    # have no value at all — not an error, and not a `None` value.
    with test_server(app) as ts:
        assert ts.get_output("dist_data").status == "silent"
        assert ts.get_output("dist_caption").status == "silent"
