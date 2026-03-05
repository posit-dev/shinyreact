from typing import Any, Sequence

from htmltools import HTMLDependency, Tag
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

    Downstream packages subclass this to accept their own return types and
    inject their own HTML dependencies::

        class render(shinyjson.render):
            extra_deps = [my_html_dependency()]

            async def transform(self, value: MyComponent) -> Any:
                return value.to_spec().to_dict()
    """

    extra_deps: Sequence[HTMLDependency] | None = None

    async def transform(self, value: Spec) -> Any:
        return value.to_dict()

    def auto_output_ui(self) -> Tag:
        # Express mode: auto-generate the output container.
        # extra_deps allows downstream subclasses to inject their JS/CSS.
        return ui(self.output_id, extra_deps=self.extra_deps)
