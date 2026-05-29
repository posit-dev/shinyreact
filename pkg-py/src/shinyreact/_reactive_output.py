from htmltools import Tag
from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._output import ui_output
from ._spec import Node


class reactive_output(Renderer[Node | Jsonifiable]):
    """Reactive output decorator for shinyreact.

    The server-side counterpart to ``useShinyOutput()`` on the React client.
    Accepts:

    * :class:`~shinyreact.Spec` — pre-flattened component tree, serialized via
      :meth:`Spec.to_dict`.
    * :class:`~shinyreact.Node` — nested component tree, flattened via
      :meth:`Node.to_spec` first.
    * Any JSON-serializable value (``dict``, ``list``, ``str``, ``int``,
      ``float``, ``None``) — passed through unchanged.

    In Shiny Express mode the decorator auto-generates a
    :func:`~shinyreact.ui_output` container at the corresponding output ID.

    Downstream packages that need to inject extra HTMLDependencies attach
    them on the UI side via ``shinyreact.ui_output(id, extra_deps=[...])``.

    Example -- plain JSON for ``useShinyOutput()``::

        @shinyreact.reactive_output
        def my_data():
            return {"key": "value", "count": 42}

    Example -- Spec-based rendering::

        @shinyreact.reactive_output
        def my_card() -> shinyreact.Spec:
            return shinyreact.Spec(
                root="card",
                elements={
                    "card": shinyreact.Element(
                        type="Card", props={"title": "Hi"}
                    ),
                },
            )
    """

    async def transform(self, value: Node | Jsonifiable) -> Jsonifiable:
        if isinstance(value, Node):
            return value.to_spec().to_dict()
        if isinstance(value, Spec):
            return value.to_dict()
        return value

    def auto_output_ui(self) -> Tag:
        return ui_output(self.output_id)
