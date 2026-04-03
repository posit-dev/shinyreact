from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Element:
    type: str
    props: dict[str, Any]
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "props": self.props, "children": self.children}


@dataclass
class Spec:
    root: str
    elements: dict[str, Element]

    def __post_init__(self) -> None:
        if self.root not in self.elements:
            keys = list(self.elements.keys())
            raise ValueError(f"root '{self.root}' not found in elements keys: {keys}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "elements": {key: elem.to_dict() for key, elem in self.elements.items()},
        }


@dataclass
class Node:
    """A nested component node that can be flattened into a :class:`Spec`.

    Unlike :class:`Element`, children are nested ``Node`` objects rather than
    string IDs.  Call :meth:`to_spec` to walk the tree, assign auto-generated
    element keys, and produce a flat :class:`Spec`.
    """

    type: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list[Node] = field(default_factory=list)

    def to_spec(self) -> Spec:
        """Flatten this node tree into a :class:`Spec` with auto-generated keys."""
        elements: dict[str, Element] = {}
        counter = 0

        def _walk(node: Node) -> str:
            nonlocal counter
            counter += 1
            key = f"auto_{counter:03d}"
            child_keys = [_walk(child) for child in node.children]
            elements[key] = Element(
                type=node.type, props=node.props, children=child_keys
            )
            return key

        root_key = _walk(self)
        return Spec(root=root_key, elements=elements)
