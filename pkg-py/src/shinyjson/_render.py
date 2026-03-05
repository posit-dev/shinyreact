from typing import Any

from htmltools import Tag
from shiny.render.renderer import Renderer

from ._output import ui
from ._spec import Spec


class render(Renderer[Spec]):
    """Render a :class:`~shinyjson.Spec` as a reactive Shiny JSON output.

    Use this decorator on a server function that returns a
    :class:`~shinyjson.Spec` instance. The spec is serialized and sent to the
    browser, where the ``shinyjson`` Shiny output binding renders it using all
    registered downstream components.

    Example::

        @shinyjson.render
        def my_output() -> shinyjson.Spec:
            return shinyjson.Spec(
                root="card",
                elements={
                    "card": shinyjson.Element(
                        type="Card", props={"title": "Hi"}
                    ),
                },
            )

    Downstream packages subclass this to accept their own return types::

        class render(shinyjson.render):
            async def transform(self, value: MyComponent) -> Any:
                return value.to_spec().to_dict()
    """

    async def transform(self, value: Spec) -> Any:
        return value.to_dict()

    def auto_output_ui(self) -> Tag:
        # Express mode: auto-generate the output container
        return ui(self.output_id)
