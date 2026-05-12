"""Python factory functions for {{Name}} components.

Each factory returns a ``shinyreact.Node`` with a ``{{prefix}}:``-namespaced type
string. Currently scaffolded with one stub factory; add more by following the
pattern.
"""

import shinyreact


def {{stub}}(label: str, *, input_id: str) -> shinyreact.Node:
    """Render the stub {{Stub}} bound to a Shiny action-button input."""
    return shinyreact.Node(
        type="{{prefix}}:{{Stub}}",
        props={"label": label, "input_id": input_id},
    )


# Uncomment and adapt if the package needs to ship its own object type that
# render functions return and the JS side consumes via useShinyOutputValue.
# Per RFC §4.4, only subclass when there is package-specific transform logic.
#
# from typing import Any
#
# class render(shinyreact.reactive_output):
#     async def transform(self, value: Any) -> Any:
#         # e.g. return value.to_spec().to_dict()
#         return value
