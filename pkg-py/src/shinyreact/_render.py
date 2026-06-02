from __future__ import annotations

from warnings import warn

from htmltools import Tag, TagList
from shiny.types import Jsonifiable

from ._spec import Node, serialize_ui


def _should_walk(value: object) -> bool:
    """True when ``value`` is htmltools/Node content to walk into the JSON wire tree.

    Bare ``str`` / ``bytes`` are excluded so JSON-string outputs in the
    ``ui.tsx`` pattern pass through unchanged.
    """
    if isinstance(value, (str, bytes)):
        return False
    if isinstance(value, (Node, Tag, TagList)):
        return True
    return hasattr(value, "tagify")


def walk_or_passthrough(value: object, output_id: str) -> Jsonifiable:
    """Walk htmltools/``Node`` content into the JSON wire tree, else pass through.

    Shared by ``render_react`` and ``reactive_output``. Emits a warning when a
    walked tree carries ``HTMLDependency`` objects that cannot reach ``<head>``
    after the page has rendered.
    """
    if _should_walk(value):
        payload, deps = serialize_ui(value)
        if deps:
            names = ", ".join(d.name for d in deps)
            warn(
                f"shinyreact: '{output_id}' returned content carrying "
                f"HTMLDependency objects ({names}) that cannot be injected "
                "after the page has rendered. Declare them up-front via "
                "output_react(..., extra_deps=[...]) or at the page level.",
                UserWarning,
                # stacklevel=2: Shiny calls transform() internally, so this
                # can't reach user code anyway.
                stacklevel=2,
            )
        return payload
    return value  # type: ignore[return-value]
