"""Pins the server-side `(test)` leaves in this example's FEATURES.md.

The claim these exist to defend is a cross-language one: Python's
dependency-free binner and R's `hist()` must produce the same histogram for the
same data, because `www/ui.js` draws whichever one answers. The golden counts
below are asserted verbatim in R too — see
`tests/test-histogram.R` next to it, which the R package's test suite runs.

Only `faithful.py` is importable; `app.py` calls `set_react_page()` at module
scope, so the two outputs' logic cannot be unit tested. That factoring — pure
functions in a module beside the app — is what makes example server logic
testable at all.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE))

from faithful import histogram, waiting  # noqa: E402

# bins = 9 over the 272 waiting times. Mirrored in
# tests/test-histogram.R and tests/ui.test.ts next to it.
COUNTS_9 = [16, 37, 30, 16, 14, 57, 67, 29, 6]
COUNTS_30 = [
    1, 8, 7, 10, 6, 12, 15, 7, 4, 13, 4, 7, 3, 3, 3,
    9, 8, 6, 17, 27, 18, 13, 26, 16, 8, 6, 9, 2, 3, 1,
]  # fmt: skip


def test_dataset_shape():
    assert len(waiting) == 272
    assert min(waiting) == 43.0
    assert max(waiting) == 96.0


@pytest.mark.parametrize("bins", [1, 2, 9, 30, 50])
def test_lengths_and_total(bins: int):
    h = histogram(waiting, bins)
    assert len(h["breaks"]) == bins + 1
    assert len(h["counts"]) == bins
    # Every observation lands in exactly one bin.
    assert sum(h["counts"]) == 272


def test_breaks_span_the_data_exactly():
    h = histogram(waiting, 9)
    assert h["breaks"][0] == 43.0
    assert h["breaks"][-1] == pytest.approx(96.0)


def test_one_bin_holds_everything():
    h = histogram(waiting, 1)
    assert h["counts"] == [272]
    assert h["breaks"] == [43.0, 96.0]


def test_matches_r_hist_counts():
    assert histogram(waiting, 9)["counts"] == COUNTS_9
    assert histogram(waiting, 30)["counts"] == COUNTS_30


def test_bins_are_half_open_with_an_inclusive_first_bin():
    # R's hist(): (lo, hi], except the first bin, which includes lo. A value on
    # an interior break belongs to the bin below it, and the maximum belongs to
    # the last bin rather than falling off the end.
    values = [0.0, 5.0, 10.0]
    assert histogram(values, 2)["counts"] == [2, 1]
