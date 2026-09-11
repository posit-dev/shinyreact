import csv
import math
import subprocess
import sys
from pathlib import Path

from shiny import App, Inputs, Outputs, Session
from shinyreact import page_bare, page_react_dep, reactive_output

_APP_DIR = Path(__file__).parent

# The bundle is gitignored, so a fresh clone has no `www/` at all. Build it on
# first run instead of greeting the reader with a stack trace — same as
# examples/09-hmr, the other npm-tier example.
if not (_APP_DIR / "www" / "ui.js").exists():
    print("www/ui.js not found -- building the client bundle...", file=sys.stderr)
    # `@posit-dev/shinyreact` is a `file:../../pkg-js` dep whose exports point
    # at `dist-npm/`, which is not committed -- so the package has to be built
    # before this app's own build can resolve it.
    _pkg_js = _APP_DIR.parent.parent / "pkg-js"
    if not (_pkg_js / "dist-npm").exists():
        subprocess.run(["npm", "install"], cwd=_pkg_js, check=True)
        subprocess.run(["npm", "run", "build"], cwd=_pkg_js, check=True)
    subprocess.run(["npm", "install"], cwd=_APP_DIR, check=True)
    subprocess.run(["npm", "run", "build"], cwd=_APP_DIR, check=True)

with (_APP_DIR / "faithful.csv").open(newline="") as f:
    waiting = [float(row["waiting"]) for row in csv.DictReader(f)]


def histogram(values: list[float], bins: int) -> dict[str, list[float] | list[int]]:
    """Equal-width binning matching R's `hist()`: bins are (lo, hi], first inclusive."""
    lo, hi = min(values), max(values)
    width = (hi - lo) / bins
    breaks = [lo + i * width for i in range(bins + 1)]
    counts = [0] * bins
    for v in values:
        idx = math.ceil((v - lo) / width) - 1
        counts[min(max(idx, 0), bins - 1)] += 1
    return {"breaks": breaks, "counts": counts}


# The whole page: Shiny's own dependencies plus this app's bundle, served as
# an HTMLDependency out of www/. No shinyreact JS is injected — the client
# runtime is inside www/ui.js, which imports `@posit-dev/shinyreact`. With no
# server-side bundle there is also no #shinyreact-config tag and no protocol
# handshake; page_bare() is the one page entry point that emits neither.
ui = page_bare(
    page_react_dep(src_dir=_APP_DIR / "www", name="npm-local"),
    title="Old Faithful",
)


def server(input: Inputs, output: Outputs, session: Session):
    @reactive_output
    def dist_data():
        return histogram(waiting, input.bins())

    @reactive_output
    def dist_caption():
        n = input.bins()
        return f"{len(waiting)} eruptions in {n} bin{'' if n == 1 else 's'}"


app = App(ui, server)
