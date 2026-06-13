from __future__ import annotations

from pathlib import Path

from htmltools import HTMLDependency

# The built JS/CSS live in the shared ui-frameworks/shadcn/www/ directory, which
# feeds the JS, Python, and R packages alike and stays fresh in a source checkout,
# so prefer it. Installed wheels have no such directory (only the copy hatch_build
# vendors at shinyshadcn/www/), so fall back to the bundled copy. Preferring
# shared avoids serving a stale build-time copy after a dev rebuild.
_shared = Path(__file__).parent.parent.parent.parent / "www"
_bundled = Path(__file__).parent / "www"
_www = _shared if (_shared / "shadcn.js").exists() else _bundled


def _dep() -> HTMLDependency:
    js = _www / "shadcn.js"
    version = str(int(js.stat().st_mtime)) if js.exists() else "0"
    return HTMLDependency(
        name="shinyshadcn",
        version=version,
        source={"subdir": str(_www)},
        script={"src": "shadcn.js", "defer": ""},
        stylesheet={"href": "style.css"},
    )
