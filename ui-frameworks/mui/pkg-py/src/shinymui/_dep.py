from __future__ import annotations

from pathlib import Path

from htmltools import HTMLDependency

# Installed wheels bundle the built assets at shinymui/www/ (copied from the
# shared ui-frameworks/mui/www/ by hatch_build.py). A source checkout used via
# sys.path.insert has no such copy, so fall back to the shared directory.
_bundled = Path(__file__).parent / "www"
_shared = Path(__file__).parent.parent.parent.parent / "www"
_www = _bundled if (_bundled / "mui.js").exists() else _shared


def _dep() -> HTMLDependency:
    js = _www / "mui.js"
    version = str(int(js.stat().st_mtime)) if js.exists() else "0"
    return HTMLDependency(
        name="shinymui",
        version=version,
        source={"subdir": str(_www)},
        script={"src": "mui.js", "defer": ""},
    )
