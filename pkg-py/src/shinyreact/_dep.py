from pathlib import Path
from typing import Literal

from htmltools import HTMLDependency, TagChild, TagList

from ._bookmark import _config_script_tag

_WWW_DIR = Path(__file__).parent / "www"
_SHINYREACT_JS_PATH = _WWW_DIR / "shinyreact.js"

# Who supplies shinyreact.js (and shinyreact.css) to the page.
ShinyreactJs = Literal["server", "client"]
_SHINYREACT_JS_VALUES = ("server", "client")


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


def _serves_bundle(shinyreact_js: ShinyreactJs) -> bool:
    """Validate ``shinyreact_js=`` and say whether the page attaches the bundle.

    The one place the value is checked, so every entry point rejects a typo the
    same way. A bad value is a startup error rather than a page that silently
    loads no hooks.
    """
    if shinyreact_js not in _SHINYREACT_JS_VALUES:
        expected = ", ".join(repr(v) for v in _SHINYREACT_JS_VALUES)
        raise ValueError(
            f"shinyreact_js={shinyreact_js!r} is not valid. Expected one of "
            f'{expected}. Use "server" when the shinyreact package should serve '
            "shinyreact.js (the default, and what a no-build app needs), and "
            '"client" when your own bundle imports @posit/shinyreact and '
            "therefore ships its own copy."
        )
    return shinyreact_js == "server"


def _dep_page(shinyreact_js: ShinyreactJs = "server") -> TagChild:
    """Page-level shinyreact dependency: bundle + ``#shinyreact-config`` tag.

    Use from page entry points (``page_react_html``, ``set_react_page``'s page
    function) — the config tag carries the protocol version on every page and
    the bookmark restore payload when one is active.

    ``shinyreact_js="client"`` omits ``shinyreact.js`` / ``shinyreact.css`` for
    npm-tier pages, whose client bundle ships its own copy. The config tag is
    always emitted: the npm client hard-errors without it.
    """
    bundle = _dep() if _serves_bundle(shinyreact_js) else None
    return TagList(bundle, _config_script_tag())
