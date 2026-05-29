from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from htmltools import HTML, HTMLDependency, MetadataNode, Tag, TagList

# HTML attribute name -> React prop name. Anything not listed (including
# data-* and aria-*) passes through verbatim — React accepts those.
_ATTR_MAP: dict[str, str] = {
    "class": "className",
    "for": "htmlFor",
    "tabindex": "tabIndex",
    "colspan": "colSpan",
    "rowspan": "rowSpan",
    "maxlength": "maxLength",
    "readonly": "readOnly",
    "autofocus": "autoFocus",
    "contenteditable": "contentEditable",
}


def _translate_attrs(attrs: dict[str, Any]) -> dict[str, Any]:
    return {_ATTR_MAP.get(k, k): v for k, v in attrs.items()}


def _walk_all(children: Iterable[Any], deps: list[HTMLDependency]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for child in children:
        out.extend(_walk(child, deps))
    return out


def _walk(child: Any, deps: list[HTMLDependency]) -> list[dict[str, Any]]:
    """Convert one TagChild into zero or more wire nodes; collect HTMLDependency.

    Returns a list because ``TagList`` / sequences flatten to several nodes and
    ``None`` / metadata flatten to none.
    """
    if child is None:
        return []
    if isinstance(child, Node):
        return [child._to_wire(deps)]
    if isinstance(child, Tag):
        return [
            {
                "type": "tag",
                "name": child.name,
                "props": _translate_attrs(dict(child.attrs)),
                "children": _walk_all(child.children, deps),
            }
        ]
    if isinstance(child, TagList):
        return _walk_all(child, deps)
    if isinstance(child, HTML):
        return [{"type": "html", "html": str(child)}]
    if isinstance(child, HTMLDependency):
        deps.append(child)
        return []
    if isinstance(child, MetadataNode):
        # Other metadata (e.g. head content) has no spec representation.
        return []
    if isinstance(child, str):
        return [{"type": "text", "value": child}]
    if isinstance(child, (int, float)):
        return [{"type": "text", "value": str(child)}]
    if isinstance(child, (list, tuple)):
        return _walk_all(child, deps)
    if hasattr(child, "tagify"):
        return _walk(child.tagify(), deps)
    return [{"type": "text", "value": str(child)}]


def serialize_ui(value: Any) -> tuple[Any, list[HTMLDependency]]:
    """Walk a TagChild tree into a wire payload + harvested dependencies.

    The payload is a single wire node when the walk yields exactly one node,
    a list of nodes when it yields several (e.g. a ``TagList`` with multiple
    top-level children), or an empty list when it yields none (e.g. an empty
    ``TagList`` or ``None``) — the renderer treats an empty list as "render
    nothing".
    """
    deps: list[HTMLDependency] = []
    nodes = _walk(value, deps)
    payload: Any = nodes[0] if len(nodes) == 1 else nodes
    return payload, deps


@dataclass
class Node:
    """A React-component node that interleaves with htmltools content.

    ``type`` is the registered component name. ``children`` may mix nested
    ``Node`` objects, htmltools ``Tag`` / ``TagList`` / ``HTML``, and strings;
    serialization walks them into a single JSON wire tree.
    """

    type: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list[Any] = field(default_factory=list)

    def _to_wire(self, deps: list[HTMLDependency]) -> dict[str, Any]:
        return {
            "type": "react",
            "name": self.type,
            "props": self.props,
            "children": _walk_all(self.children, deps),
        }

    def tagify(self) -> "Node":
        """Satisfy the htmltools ``Tagifiable`` protocol.

        Returning ``self`` lets ``TagList`` (and any other htmltools container)
        accept a ``Node`` as a child without converting it to HTML.  The actual
        serialization is handled by :meth:`_to_wire` when the walker encounters
        this node.
        """
        return self

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the wire tree, discarding any harvested dependencies.

        If the node tree contains ``HTMLDependency`` children, use
        :func:`serialize_ui` (or :meth:`serialize`, added later) instead to
        harvest them.
        """
        return self._to_wire([])


# ---------------------------------------------------------------------------
# Backward-compatible stubs — kept so existing imports in __init__.py and
# _reactive_output.py do not break while later tasks migrate those files.
# These will be removed in Task 5.
# ---------------------------------------------------------------------------


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
