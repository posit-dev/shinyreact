from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable


class render_json(Renderer[Jsonifiable]):
    """Send a JSON-serializable value to the client.

    Use on a server function whose return value is consumed by a
    ``useShinyOutput()`` hook on the client. The value is passed through
    unchanged — no transformation, no UI generation.

    Example::

        @shinyjson.render_json
        def my_data():
            return {"title": "Hello", "count": 42}
    """

    async def transform(self, value: Jsonifiable) -> Jsonifiable:
        return value
