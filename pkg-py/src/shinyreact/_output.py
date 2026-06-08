from pathlib import Path
from typing import Sequence

from htmltools import HTMLDependency, Tag, TagChild, TagList, div

from ._bookmark import _restore_script_tag

_WWW_DIR = Path(__file__).parent / "www"
_SHINYREACT_JS_PATH = _WWW_DIR / "shinyreact.js"


def _file_mtime_int(path: Path) -> int | None:
    """Return the file's mtime in whole seconds, or None if it doesn't exist."""
    try:
        return int(path.stat().st_mtime)
    except FileNotFoundError:
        return None


def _dep() -> HTMLDependency:
    # Use the bundle's mtime as the version so browsers re-fetch after a
    # `make update-dist`. Falls back to a fixed version if the bundle is
    # missing (e.g. in a partially-built dev checkout).
    mtime = _file_mtime_int(_SHINYREACT_JS_PATH)
    version = str(mtime) if mtime is not None else "0.1.0"
    return HTMLDependency(
        name="shinyreact",
        version=version,
        source={"subdir": str(_WWW_DIR)},
        script={"src": "shinyreact.js", "defer": ""},
        stylesheet={"href": "shinyreact.css"},
    )


def _dep_page() -> TagChild:
    """Page-level shinyreact dependency: bundle + bookmark restore script.

    Use from page entry points (``page_react``, ``set_react_page``'s page
    function). Per-output consumers (``output_react``) should keep calling
    ``_dep()`` — they do not carry page-level restore state.
    """
    restore = _restore_script_tag()  # may be None
    return TagList(_dep(), restore) if restore is not None else _dep()


def output_react(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag:
    """Create a Shiny output placeholder for a shinyreact ``render_react`` renderer.

    Args:
        id: The output ID. Must match the server-side ``@shinyreact.render_react``
            function name.
        extra_deps: Additional HTML dependencies to include. Used by downstream
            packages to inject their own JS/CSS (e.g. ``shinyshadcn``).

    Returns:
        A ``<div>`` tag that the shinyreact Shiny output binding renders into.
    """
    return div(
        _dep(),
        *(extra_deps or []),
        id=id,
        class_="shinyreact-output",
    )
