from typing import Sequence

from htmltools import HTMLDependency, Tag
from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._output import ui
from ._spec import Spec


class render(Renderer[Spec | Jsonifiable]):
    """Render a :class:`~shinyjson.Spec` or raw JSON data as a reactive Shiny output.

    Use this decorator on a server function that returns a
    :class:`~shinyjson.Spec` instance **or** any JSON-serializable value
    (``dict``, ``list``, ``str``, ``int``, ``float``, ``None``).

    When the return value is a :class:`~shinyjson.Spec`, it is serialized via
    :meth:`Spec.to_dict` before being sent to the browser.  Any other
    JSON-serializable value is passed through unchanged, which is useful for
    ``useShinyOutput()`` hooks on the React side that consume arbitrary data.

    Example -- Spec-based rendering::

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

    Example -- raw JSON for ``useShinyOutput()``::

        @shinyjson.render
        def my_data():
            return {"key": "value", "count": 42}

    Downstream packages subclass this to accept their own return types and
    inject their own HTML dependencies::

        class render(shinyjson.render):
            extra_deps = [my_html_dependency()]

            async def transform(self, value: MyComponent) -> Jsonifiable:
                return value.to_spec().to_dict()
    """

    extra_deps: Sequence[HTMLDependency] | None = None

    async def transform(self, value: Spec | Jsonifiable) -> Jsonifiable:
        if isinstance(value, Spec):
            return value.to_dict()
        # Raw JSON-serializable data -- pass through for useShinyOutput() consumption
        return value

    def auto_output_ui(self) -> Tag:
        # Express mode: auto-generate the output container.
        # extra_deps allows downstream subclasses to inject their JS/CSS.
        return ui(self.output_id, extra_deps=self.extra_deps)
