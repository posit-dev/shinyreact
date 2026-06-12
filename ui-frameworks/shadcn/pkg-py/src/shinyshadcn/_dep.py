from __future__ import annotations

from pathlib import Path

from htmltools import HTMLDependency

# The built JS/CSS live in the shared ui-frameworks/shadcn/www/ directory, which
# feeds the JS, Python, and R packages alike. Installed wheels force-include a
# copy at shinyshadcn/www/ (see pyproject.toml); a source checkout used via
# sys.path.insert has no such copy, so fall back to the shared directory.
_bundled = Path(__file__).parent / "www"
_shared = Path(__file__).parent.parent.parent.parent / "www"
_www = _bundled if (_bundled / "shadcn.js").exists() else _shared


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
