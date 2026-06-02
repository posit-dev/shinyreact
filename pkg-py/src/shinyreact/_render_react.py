from __future__ import annotations

from htmltools import Tag, TagChild
from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._output import output_react
from ._render import walk_or_passthrough
from ._spec import Node


class render_react(Renderer["Node | TagChild"]):
    """Render a React component tree to a shinyreact output (the ``app.py`` pattern).

    Assign to ``output[id]`` where the UI has a matching ``output_react(id)``
    placeholder. Accepts a :class:`~shinyreact.Node` tree and any htmltools
    ``TagChild`` (``Tag``, ``TagList``, ``Tagifiable``, ``HTML``, scalar
    children) — walked into the JSON wire tree.

    Dependencies harvested from a walked tree cannot reach ``<head>`` after the
    page has rendered; declare them up-front via
    ``output_react(..., extra_deps=[...])`` or at the page level. A warning is
    emitted if a returned tree carries any.
    """

    async def transform(self, value: Node | TagChild) -> Jsonifiable:
        return walk_or_passthrough(value, self.output_id)

    def auto_output_ui(self) -> Tag:
        return output_react(self.output_id)
