from pathlib import Path

from htmltools import HTMLDependency

_www_dir = Path(__file__).parent / "www"


def dep() -> HTMLDependency:
    """HTMLDependency for the shinymui JS bundle.

    Versioned by mtime of the bundled JS file so browsers re-fetch when the
    bundle is rebuilt during development. A real package would pin to its
    release version.
    """
    bundle = _www_dir / "shinymui.js"
    version = str(int(bundle.stat().st_mtime)) if bundle.exists() else "0"
    return HTMLDependency(
        name="shinymui",
        version=version,
        source={"subdir": str(_www_dir)},
        script={"src": "shinymui.js", "defer": ""},
    )
