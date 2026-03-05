from pathlib import Path
from typing import Sequence

from htmltools import HTMLDependency, Tag, div


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyjson",
        version="0.1.0",
        source={"subdir": str(Path(__file__).parent / "www")},
        script={"src": "shinyjson.js"},
        stylesheet={"href": "shinyjson.css"},
    )


def ui(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag:
    """Create a Shiny output placeholder for a shinyjson renderer.

    Args:
        id: The output ID. Must match the server-side ``@shinyjson.render``
            function name.
        extra_deps: Additional HTML dependencies to include. Used by downstream
            packages to inject their own JS/CSS (e.g. ``shinyshadcn``).

    Returns:
        A ``<div>`` tag that the shinyjson Shiny output binding renders into.
    """
    return div(
        _dep(),
        *(extra_deps or []),
        id=id,
        class_="shinyjson-output",
    )
