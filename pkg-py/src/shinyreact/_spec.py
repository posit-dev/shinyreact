from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from htmltools import HTML, HTMLDependency, MetadataNode, Tag, Tagified, TagList

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


# Characters that are dangerous inside an HTML <script> element or illegal
# unescaped in a JavaScript string literal, each mapped to its JSON \uXXXX
# escape. JSON.parse() (and json.loads) decode the escapes back to the original
# characters, so the round-trip is lossless. Escaping "<", ">", and "&"
# neutralizes "</script>", "<!--", "-->", and "<![CDATA[" breakouts; U+2028 and
# U+2029 are valid in JSON but illegal unescaped in a JS string literal.
# Mirrors R's `.script_safe_json()` in pkg-r/R/wire.R — keep the two in lockstep.
_SCRIPT_SAFE_ESCAPES = {
    "<": "\\u003c",
    ">": "\\u003e",
    "&": "\\u0026",
    " ": "\\u2028",
    " ": "\\u2029",
}


def script_safe_json(value: Any) -> str:
    """Serialize ``value`` to JSON safe to embed in an HTML ``<script>``.

    Produces ``json.dumps(value)`` with the script-dangerous characters
    (``<``, ``>``, ``&``, U+2028, U+2029) replaced by their ``\\uXXXX`` JSON
    escapes. The escapes are decoded back to the original characters by
    ``JSON.parse`` on the client, so embedding is lossless.
    """
    out = json.dumps(value)
    for char, escape in _SCRIPT_SAFE_ESCAPES.items():
        out = out.replace(char, escape)
    return out


def _walk_all(
    children: Iterable[Any], deps: list[HTMLDependency]
) -> list[dict[str, Any]]:
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

    def serialize(self) -> tuple[dict[str, Any], list[HTMLDependency]]:
        """Serialize to the wire tree plus harvested HTML dependencies."""
        deps: list[HTMLDependency] = []
        return self._to_wire(deps), deps

    def tagify(self) -> Tagified:
        """Render as a static `.shinyreact-static` mount carrying its spec.

        Makes ``Node`` a ``Tagifiable`` so it can be embedded directly in page
        chrome (e.g. ``page_react(tags.div(Node(...)))``). The mount has no id
        and is not a Shiny output; the JS bundle seeds it from the child script
        at load time. The inline JSON is linked to its mount by DOM adjacency.
        """
        from htmltools import tags

        from ._output import _dep

        node, deps = self.serialize()
        # Serialize script-safe so a payload containing "</script>" (or "<!--",
        # U+2028/U+2029, …) cannot break out of the inline <script>. The escapes
        # are decoded back by JSON.parse on the client. See script_safe_json.
        spec_json = script_safe_json(node)
        # htmltools requires a `.tagify()` implementation to return a fully
        # tagified value; call `.tagify()` on the assembled TagList so nested
        # Tags (the mount div, the dep) are tagified too.
        return TagList(
            _dep(),
            *deps,
            tags.div(
                tags.script(spec_json, type="application/json"),
                class_="shinyreact-static",
            ),
        ).tagify()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the wire tree, discarding any harvested dependencies.

        If the node tree contains ``HTMLDependency`` children, use
        :func:`serialize_ui` (or :meth:`serialize`) instead to
        harvest them.
        """
        return self._to_wire([])
