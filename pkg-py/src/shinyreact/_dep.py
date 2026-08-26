from pathlib import Path

from htmltools import HTMLDependency, TagChild, TagList

from ._bookmark import _config_script_tag

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
    """Page-level shinyreact dependency: bundle + ``#shinyreact-config`` tag.

    Use from page entry points (``page_react_html``, ``set_react_page``'s page
    function) — the config tag carries the protocol version on every page and
    the bookmark restore payload when one is active.
    """
    return TagList(_dep(), _config_script_tag())
