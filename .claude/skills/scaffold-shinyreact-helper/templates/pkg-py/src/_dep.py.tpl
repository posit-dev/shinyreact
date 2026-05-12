from pathlib import Path

from htmltools import HTMLDependency

_www_dir = Path(__file__).parent / "www"


def dep() -> HTMLDependency:
    """HTMLDependency for the {{pkg}} JS bundle.

    Versioned by mtime of the bundled JS file so browsers re-fetch when the
    bundle is rebuilt during development. A real package would pin to its
    release version.
    """
    bundle = _www_dir / "{{pkg}}.js"
    version = str(int(bundle.stat().st_mtime)) if bundle.exists() else "0"
    return HTMLDependency(
        name="{{pkg}}",
        version=version,
        source={"subdir": str(_www_dir)},
        script={"src": "{{pkg}}.js", "defer": ""},
    )
