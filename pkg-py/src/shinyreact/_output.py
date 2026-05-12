from pathlib import Path
from typing import Sequence

from htmltools import HTMLDependency, Tag, TagChild, TagList, div

from ._bookmark import _restore_script_tag


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyreact",
        version="0.1.0",
        source={"subdir": str(Path(__file__).parent / "www")},
        script={"src": "shinyreact.js", "defer": ""},
        stylesheet={"href": "shinyreact.css"},
    )


def _dep_page() -> TagChild:
    """Page-level shinyreact dependency: bundle + bookmark restore script.

    Use from page entry points (``page_react``, ``set_react_page``'s page
    function). Per-output consumers (``ui_output``) should keep calling
    ``_dep()`` — they do not carry page-level restore state.
    """
    restore = _restore_script_tag()  # may be None
    return TagList(_dep(), restore) if restore is not None else _dep()


def ui_output(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag:
    """Create a Shiny output placeholder for a shinyreact renderer.

    Args:
        id: The output ID. Must match the server-side ``@shinyreact.reactive_output``
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
