"""Old Faithful waiting times + a dependency-free histogram binner.

Shared by `app.py` (Express) and `app-core.py` (Core). R's `app.R` uses the
`faithful` dataset built into base R and `hist(..., plot = FALSE)` instead;
`faithful.csv` is that same dataset exported for the Python servers.
"""

from __future__ import annotations

import csv
from pathlib import Path

_CSV = Path(__file__).parent / "faithful.csv"

with _CSV.open(newline="") as f:
    waiting: list[float] = [float(row["waiting"]) for row in csv.DictReader(f)]


def histogram(values: list[float], bins: int) -> dict[str, list[float] | list[int]]:
    """Equal-width binning matching R's `hist()`: bins are (lo, hi], first inclusive."""
    lo, hi = min(values), max(values)
    width = (hi - lo) / bins
    breaks = [lo + i * width for i in range(bins + 1)]
    counts = [0] * bins
    for v in values:
        counts[min(int((v - lo) / width), bins - 1)] += 1
    return {"breaks": breaks, "counts": counts}
