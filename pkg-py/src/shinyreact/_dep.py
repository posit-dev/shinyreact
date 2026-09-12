from pathlib import Path
from typing import Literal

from htmltools import HTMLDependency, TagChild, TagList

from ._bookmark import _config_script_tag

_WWW_DIR = Path(__file__).parent / "www"

# `@posit-dev/shinyreact`'s version, i.e. the release of the bundle in `www/`.
# It is the shinyreact HTMLDependency's version, so
# `/lib/shinyreact-0.1.1/shinyreact.js` names the JS release being served and
# an npm-tier app can read the page source to see whether its bundled copy
# matches the server's. Bump alongside `pkg-js/package.json`; `test_dep.py`
# pins the two together. Mirrors R's `.shinyreact_js_version`.
_SHINYREACT_JS_VERSION = "0.1.1"

# Only reachable from a repo checkout (editable install), never from an
# installed wheel. Its presence is the "dev checkout" signal for
# `_bundle_version()`.
_JS_PACKAGE_JSON = Path(__file__).parents[3] / "pkg-js" / "package.json"

# Who supplies shinyreact.js (and shinyreact.css) to the page.
ShinyreactJs = Literal["server", "client"]
_SHINYREACT_JS_VALUES = ("server", "client")


def _file_mtime_int(path: Path) -> int | None:
    """Return the file's mtime in whole seconds, or None if it doesn't exist."""
    try:
        return int(path.stat().st_mtime)
    except FileNotFoundError:
        return None


def _bundle_version() -> str:
    """``_SHINYREACT_JS_VERSION``, suffixed with the bundle's mtime in a dev checkout.

    An installed package serves ``/lib/shinyreact-0.1.1/``. In the repo
    checkout it is ``/lib/shinyreact-0.1.1.<mtime>/`` instead, so a
    ``make update-dist`` still cache-busts while the URL still names the release.
    Mirrors R's ``.bundle_version()``.
    """
    if _JS_PACKAGE_JSON.is_file():
        mtime = _file_mtime_int(_WWW_DIR / "shinyreact.js")
        if mtime is not None:
            return f"{_SHINYREACT_JS_VERSION}.{mtime}"
    return _SHINYREACT_JS_VERSION


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyreact",
        version=_bundle_version(),
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
            '"client" when your own bundle imports @posit-dev/shinyreact and '
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
    always emitted: it carries the protocol version and any bookmark restore
    payload.
    """
    bundle = _dep() if _serves_bundle(shinyreact_js) else None
    return TagList(bundle, _config_script_tag())
