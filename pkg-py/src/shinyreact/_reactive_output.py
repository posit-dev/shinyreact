from __future__ import annotations

from warnings import warn

from htmltools import Tag, TagList
from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._output import ui_output
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


class reactive_output(Renderer["Node | Jsonifiable"]):
    """Reactive output for shinyreact.

    Accepts:

    * :class:`~shinyreact.Node` and any htmltools ``TagChild`` (``Tag``,
      ``TagList``, ``Tagifiable``) — walked into the JSON wire tree.
    * Any JSON-serializable value (``dict``, ``list``, ``str``, ``int``,
      ``float``, ``None``) — passed through unchanged for
      ``useShinyOutputValue()``.

    Dependencies harvested from a walked tree cannot reach ``<head>`` after
    the page has rendered; declare them up-front via
    ``ui_output(..., extra_deps=[...])`` or at the page level. A warning is
    emitted if a returned tree carries any.
    """

    async def transform(self, value: object) -> Jsonifiable:
        if _should_walk(value):
            payload, deps = serialize_ui(value)
            if deps:
                names = ", ".join(d.name for d in deps)
                warn(
                    f"shinyreact: '{self.output_id}' returned content carrying "
                    f"HTMLDependency objects ({names}) that cannot be injected "
                    "after the page has rendered. Declare them up-front via "
                    "ui_output(..., extra_deps=[...]) or at the page level.",
                    UserWarning,
                    # stacklevel=2: Shiny calls transform() internally, so this can't reach user code
                    stacklevel=2,
                )
            return payload
        return value  # type: ignore[return-value]

    def auto_output_ui(self) -> Tag:
        return ui_output(self.output_id)
