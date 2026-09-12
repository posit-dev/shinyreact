from __future__ import annotations

from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable


class reactive_output(Renderer["Jsonifiable"]):
    """Publish a reactive JSON value to the client (the ``ui.tsx`` pattern).

    Assign to ``output[id]`` where a React client reads the value with
    ``useShinyOutputValue()``. There is no UI placeholder: ``auto_output_ui()``
    inherits the base implementation, which returns ``None``.

    Accepts any JSON-serializable value (``dict``, ``list``, ``str``, ``int``,
    ``float``, ``bool``, ``None``), passed through unchanged.
    """

    async def transform(self, value: Jsonifiable) -> Jsonifiable:
        return value
