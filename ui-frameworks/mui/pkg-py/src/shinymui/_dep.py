from __future__ import annotations

from pathlib import Path

from htmltools import HTMLDependency

# The shared ui-frameworks/mui/www/ directory is the source of truth and stays
# fresh in a source checkout, so prefer it. Installed wheels have no such
# directory (only the copy hatch_build.py vendors at shinymui/www/), so fall back
# to the bundled copy. Preferring shared avoids serving a stale build-time copy
# after a dev rebuild.
_shared = Path(__file__).parent.parent.parent.parent / "www"
_bundled = Path(__file__).parent / "www"
_www = _shared if (_shared / "mui.js").exists() else _bundled


def _dep() -> HTMLDependency:
    js = _www / "mui.js"
    version = str(int(js.stat().st_mtime)) if js.exists() else "0"
    return HTMLDependency(
        name="shinymui",
        version=version,
        source={"subdir": str(_www)},
        script={"src": "mui.js", "defer": ""},
    )
