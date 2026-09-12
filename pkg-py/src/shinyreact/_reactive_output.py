from __future__ import annotations

from typing import cast

from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._json import JsonValue


class reactive_output(Renderer["JsonValue"]):
    """Publish a reactive JSON value to the client (the ``ui.tsx`` pattern).

    Assign to ``output[id]`` where a React client reads the value with
    ``useShinyOutputValue()``. There is no UI placeholder: ``auto_output_ui()``
    inherits the base implementation, which returns ``None``.

    Accepts any JSON-serializable value (``dict``, ``list``, ``str``, ``int``,
    ``float``, ``bool``, ``None``), passed through unchanged.
    """

    async def transform(self, value: JsonValue) -> Jsonifiable:
        # `JsonValue` and `Jsonifiable` describe the same runtime values; only
        # their container variance differs, so this is a re-labeling, not a
        # conversion.
        return cast(Jsonifiable, value)
