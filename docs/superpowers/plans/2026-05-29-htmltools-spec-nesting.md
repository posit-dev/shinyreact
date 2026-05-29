# Layer All The Way Down: htmltools ⇄ React spec nesting — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let htmltools content (`Tag`, `TagList`, `HTML`, strings) and shinyreact's React data model (`Node`) interleave at arbitrary depth in one tree, serialized to a discriminated-union JSON wire format and rendered by React.

**Architecture:** Replace the flat `{root, elements}` spec with a recursive tree whose nodes carry a closed `type` discriminant (`react | tag | text | html`) and a separate `name`. One Python walker (shaped like Shiny's `process_ui`) converts any mixed `TagChild` subtree into `(wire_tree, harvested_deps)`. `Node` gains `tagify()` so it is a `Tagifiable` and embeds in page chrome via a `.shinyreact-output` mount div plus a sibling inline `<script type="application/json">`. The JS renderer dispatches on `type`; a separate seeding pass renders inline specs.

**Tech Stack:** Python 3.10+ (dataclasses, htmltools, shiny), TypeScript/React 19 (Vite IIFE), pytest, vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-05-29-htmltools-spec-nesting-design.md`

**Dependency note:** This work is independent of #69. `Node` becomes a `Tagifiable` here; re-parenting it onto `UiReact(UiComponent, AllowsChildren)` is a tracked follow-up (Task 16), not a blocker.

---

## File Structure

**Python (`pkg-py/src/shinyreact/`)**
- `_spec.py` — **rewritten**. Holds `Node` (public authoring class) + the walker (`_walk`, `_walk_all`, `serialize_ui`, `_translate_attrs`) + `tagify()`. Flat `Spec`/`Element` classes removed.
- `_reactive_output.py` — **modified**. `transform` disambiguates walk-vs-passthrough and warns on render-time deps.
- `__init__.py` — **modified**. Drop `Element`, `Spec` exports; keep `Node`.

**Python tests (`pkg-py/tests/`)**
- `test_spec.py` — **rewritten** to the tree format + walker coverage.
- `test_reactive_output.py` — **rewritten** to the tree format.
- `test_walker.py` — **created**. Focused walker unit tests.
- `test_tagify.py` — **created**. `Node.tagify()` mount-div + inline-script coverage.

**JS (`js/src/`)**
- `spec.ts` — **rewritten**. Discriminated-union `Element`; `Spec = Element | Element[]`; `RegisteredComponentProps`.
- `renderer.tsx` — **rewritten**. Dispatch on `type`.
- `roots.ts` — **created**. Shared React-root cache (`getOrCreateRoot`, `roots`, `unmountRoot`), extracted from `index.ts`.
- `inline-spec.tsx` — **created**. `seedInlineSpecs()` + `installInlineSpecSeeding()`.
- `index.ts` — **modified**. Use `roots.ts`; install inline-spec seeding; binding payload type `Spec`.

**JS tests (`js/src/__tests__/`)**
- `renderer.test.tsx` — **rewritten** to the tree format.
- `inline-spec.test.tsx` — **created**.

**Examples / docs**
- `examples/app-py/14-nesting/` — **created**. Demonstrates interleaving.
- `docs/features.md`, `docs/todos.md` — **modified**.

---

## Phase 1 — Python wire format + walker

### Task 1: `Node` serializes to a `react` wire node with text children

**Files:**
- Modify: `pkg-py/src/shinyreact/_spec.py`
- Test: `pkg-py/tests/test_walker.py` (create)

- [ ] **Step 1: Write the failing test**

Create `pkg-py/tests/test_walker.py`:

```python
from shinyreact._spec import Node


def test_node_simple_react_node():
    node = Node(type="Card", props={"title": "Hi"})
    assert node.to_dict() == {
        "type": "react",
        "name": "Card",
        "props": {"title": "Hi"},
        "children": [],
    }


def test_node_string_child_becomes_text():
    node = Node(type="Card", props={}, children=["hello"])
    assert node.to_dict() == {
        "type": "react",
        "name": "Card",
        "props": {},
        "children": [{"type": "text", "value": "hello"}],
    }


def test_node_nested_react_children():
    node = Node(
        type="Page",
        props={},
        children=[Node(type="Card", props={"title": "Hi"})],
    )
    assert node.to_dict() == {
        "type": "react",
        "name": "Page",
        "props": {},
        "children": [
            {"type": "react", "name": "Card", "props": {"title": "Hi"}, "children": []}
        ],
    }


def test_node_numeric_child_becomes_text():
    node = Node(type="Card", props={}, children=[42])
    assert node.to_dict()["children"] == [{"type": "text", "value": "42"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/test_walker.py -v`
Expected: FAIL — `to_dict()` returns the old `{type, props, children}` shape (no `name`, no `react`).

- [ ] **Step 3: Rewrite `_spec.py` core**

Replace the entire contents of `pkg-py/src/shinyreact/_spec.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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


def _walk_all(children: Any, deps: list[HTMLDependency]) -> list[dict[str, Any]]:
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
        return _walk_all(list(child), deps)
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
    or a list of nodes (e.g. a ``TagList`` with several top-level children).
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

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the wire tree, discarding any harvested dependencies."""
        return self._to_wire([])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pkg-py/tests/test_walker.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyreact/_spec.py pkg-py/tests/test_walker.py
git commit -m "feat(py): Node serializes to discriminated-union wire tree (#88)"
```

---

### Task 2: Walker converts htmltools `Tag` with attribute translation

**Files:**
- Test: `pkg-py/tests/test_walker.py`
- (Implementation already present from Task 1 — this task proves it.)

- [ ] **Step 1: Write the failing test**

Append to `pkg-py/tests/test_walker.py`:

```python
from htmltools import tags


def test_tag_becomes_tag_node_with_translated_attrs():
    node = Node(type="Card", props={}, children=[
        tags.div("hi", tags.span("x", class_="hl"), class_="card", id="c1"),
    ])
    assert node.to_dict()["children"] == [
        {
            "type": "tag",
            "name": "div",
            "props": {"className": "card", "id": "c1"},
            "children": [
                {"type": "text", "value": "hi"},
                {
                    "type": "tag",
                    "name": "span",
                    "props": {"className": "hl"},
                    "children": [{"type": "text", "value": "x"}],
                },
            ],
        }
    ]


def test_input_tag_name_and_attributes_do_not_collide():
    node = Node(type="Form", props={}, children=[
        tags.input(type="text", name="email", tabindex="2", aria_label="Email"),
    ])
    child = node.to_dict()["children"][0]
    assert child["type"] == "tag"
    assert child["name"] == "input"
    assert child["props"] == {
        "type": "text",
        "name": "email",
        "tabIndex": "2",
        "aria-label": "Email",
    }
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest pkg-py/tests/test_walker.py -v`
Expected: PASS — the Task 1 implementation already handles `Tag`. (If a test fails, fix `_walk` / `_translate_attrs` before continuing.)

- [ ] **Step 3: Commit**

```bash
git add pkg-py/tests/test_walker.py
git commit -m "test(py): tag conversion + attr translation, no name/type collision (#88)"
```

---

### Task 3: Walker handles `HTML`, `TagList`, `None`, and dependency harvesting

**Files:**
- Test: `pkg-py/tests/test_walker.py`

- [ ] **Step 1: Write the failing test**

Append to `pkg-py/tests/test_walker.py`:

```python
from htmltools import HTML, HTMLDependency, TagList
from shinyreact._spec import serialize_ui


def test_html_becomes_html_node():
    node = Node(type="Card", props={}, children=[HTML("<b>bold</b>")])
    assert node.to_dict()["children"] == [{"type": "html", "html": "<b>bold</b>"}]


def test_taglist_flattens_into_parent_children():
    node = Node(type="Card", props={}, children=[TagList("a", "b")])
    assert node.to_dict()["children"] == [
        {"type": "text", "value": "a"},
        {"type": "text", "value": "b"},
    ]


def test_none_child_is_skipped():
    node = Node(type="Card", props={}, children=["a", None, "b"])
    assert node.to_dict()["children"] == [
        {"type": "text", "value": "a"},
        {"type": "text", "value": "b"},
    ]


def test_dependencies_are_harvested_not_emitted():
    dep = HTMLDependency(name="d", version="1.0", source={"subdir": "/tmp"})
    node = Node(type="Card", props={}, children=[dep, "text"])
    payload, deps = serialize_ui(node)
    # dep removed from the tree, collected on the side
    assert payload["children"] == [{"type": "text", "value": "text"}]
    assert deps == [dep]


def test_serialize_ui_single_node_unwrapped():
    payload, deps = serialize_ui(Node(type="Card"))
    assert payload["type"] == "react"
    assert deps == []


def test_serialize_ui_taglist_returns_list():
    payload, _ = serialize_ui(TagList(Node(type="A"), Node(type="B")))
    assert isinstance(payload, list)
    assert [n["name"] for n in payload] == ["A", "B"]
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest pkg-py/tests/test_walker.py -v`
Expected: PASS — Task 1 implementation covers these rows. Fix `_walk` if any fail.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/tests/test_walker.py
git commit -m "test(py): html/taglist/none/dep-harvest walker rows (#88)"
```

---

### Task 4: Walker tagifies generic `Tagifiable` children and harvests their deps

**Files:**
- Test: `pkg-py/tests/test_walker.py`

- [ ] **Step 1: Write the failing test**

Append to `pkg-py/tests/test_walker.py`:

```python
def test_generic_tagifiable_is_tagified_and_recursed():
    class Widget:
        def tagify(self):
            return tags.div("from widget", class_="w")

    node = Node(type="Card", props={}, children=[Widget()])
    assert node.to_dict()["children"] == [
        {
            "type": "tag",
            "name": "div",
            "props": {"className": "w"},
            "children": [{"type": "text", "value": "from widget"}],
        }
    ]


def test_nested_node_in_tag_in_node_folds_into_one_tree():
    node = Node(type="Card", props={}, children=[
        tags.div(Node(type="Chart", props={"data": [1, 2]})),
    ])
    assert node.to_dict()["children"] == [
        {
            "type": "tag",
            "name": "div",
            "props": {},
            "children": [
                {"type": "react", "name": "Chart", "props": {"data": [1, 2]}, "children": []}
            ],
        }
    ]
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest pkg-py/tests/test_walker.py -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/tests/test_walker.py
git commit -m "test(py): tagifiable recursion + nested fold (#88)"
```

---

### Task 5: Remove flat `Spec`/`Element`; rewrite `test_spec.py`; update exports

**Files:**
- Modify: `pkg-py/src/shinyreact/__init__.py`
- Rewrite: `pkg-py/tests/test_spec.py`

- [ ] **Step 1: Update exports**

In `pkg-py/src/shinyreact/__init__.py`, change the spec import and `__all__`:

```python
from ._spec import Node
```

and remove `"Element"` and `"Spec"` from `__all__` (keep `"Node"`):

```python
__all__ = [
    "Node",
    "page_bare",
    "page_react",
    "page_react_dep",
    "reactive_output",
    "send_message",
    "set_react_page",
    "ui_output",
]
```

- [ ] **Step 2: Rewrite `test_spec.py`**

Replace the entire contents of `pkg-py/tests/test_spec.py` with:

```python
from shinyreact import Node


def test_node_is_exported():
    assert Node(type="Card").to_dict()["type"] == "react"


def test_spec_and_element_no_longer_exported():
    import shinyreact

    assert not hasattr(shinyreact, "Spec")
    assert not hasattr(shinyreact, "Element")
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run pytest pkg-py/tests/test_spec.py pkg-py/tests/test_walker.py -v`
Expected: PASS. (`test_reactive_output.py` still imports `Element`/`Spec` and will fail — fixed in Task 6.)

- [ ] **Step 4: Commit**

```bash
git add pkg-py/src/shinyreact/__init__.py pkg-py/tests/test_spec.py
git commit -m "refactor(py)!: remove flat Spec/Element; Node is the spec surface (#88)"
```

---

## Phase 2 — reactive_output integration

### Task 6: `transform` disambiguates walk-vs-passthrough and warns on render-time deps

**Files:**
- Modify: `pkg-py/src/shinyreact/_reactive_output.py`
- Rewrite: `pkg-py/tests/test_reactive_output.py`

- [ ] **Step 1: Write the failing test**

Replace the entire contents of `pkg-py/tests/test_reactive_output.py` with:

```python
"""Tests for the reactive_output decorator with the tree wire format."""

from __future__ import annotations

import pytest
from htmltools import HTMLDependency, tags
from shinyreact import Node, reactive_output


@pytest.mark.asyncio
async def test_passthrough_dict() -> None:
    @reactive_output
    def out():
        return {"a": 1, "b": [2, 3]}

    assert await out.transform({"a": 1, "b": [2, 3]}) == {"a": 1, "b": [2, 3]}


@pytest.mark.asyncio
async def test_passthrough_primitive() -> None:
    @reactive_output
    def out():
        return 42

    assert await out.transform(42) == 42


@pytest.mark.asyncio
async def test_passthrough_string_is_json_not_text_node() -> None:
    @reactive_output
    def out():
        return "hello"

    # Top-level str is JSON passthrough, NOT a {"type": "text"} node.
    assert await out.transform("hello") == "hello"


@pytest.mark.asyncio
async def test_passthrough_list() -> None:
    @reactive_output
    def out():
        return [1, 2, 3]

    assert await out.transform([1, 2, 3]) == [1, 2, 3]


@pytest.mark.asyncio
async def test_passthrough_none() -> None:
    @reactive_output
    def out():
        return None

    assert await out.transform(None) is None


@pytest.mark.asyncio
async def test_node_is_walked_to_wire_tree() -> None:
    node = Node(type="Card", props={"title": "Hi"})

    @reactive_output
    def out():
        return node

    assert await out.transform(node) == {
        "type": "react",
        "name": "Card",
        "props": {"title": "Hi"},
        "children": [],
    }


@pytest.mark.asyncio
async def test_child_string_becomes_text_node() -> None:
    node = Node(type="Card", props={}, children=["hi"])

    @reactive_output
    def out():
        return node

    transformed = await out.transform(node)
    assert transformed["children"] == [{"type": "text", "value": "hi"}]


@pytest.mark.asyncio
async def test_tag_is_walked() -> None:
    @reactive_output
    def out():
        return tags.div("x", class_="c")

    assert await out.transform(tags.div("x", class_="c")) == {
        "type": "tag",
        "name": "div",
        "props": {"className": "c"},
        "children": [{"type": "text", "value": "x"}],
    }


@pytest.mark.asyncio
async def test_render_time_dep_emits_warning() -> None:
    dep = HTMLDependency(name="d", version="1.0", source={"subdir": "/tmp"})
    node = Node(type="Card", props={}, children=[dep])

    @reactive_output
    def out():
        return node

    with pytest.warns(UserWarning, match="HTMLDependency"):
        await out.transform(node)


def test_auto_output_ui_returns_ui_output() -> None:
    @reactive_output
    def my_card():
        return {"x": 1}

    rendered = str(my_card.auto_output_ui())
    assert "shinyreact-output" in rendered
    assert 'id="my_card"' in rendered


def test_no_extra_deps_attribute() -> None:
    assert not hasattr(reactive_output, "extra_deps")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/test_reactive_output.py -v`
Expected: FAIL — `transform` still imports/returns via the old `Spec`/`Node.to_spec()` path; `test_node_is_walked_to_wire_tree` and `test_render_time_dep_emits_warning` fail.

- [ ] **Step 3: Rewrite `_reactive_output.py`**

Replace the contents of `pkg-py/src/shinyreact/_reactive_output.py` with:

```python
from __future__ import annotations

from warnings import warn

from htmltools import Tag, TagList
from shiny.render.renderer import Renderer
from shiny.types import Jsonifiable

from ._output import ui_output
from ._spec import Node, serialize_ui


def _should_walk(value: object) -> bool:
    """True when ``value`` is htmltools/Node content to serialize as a spec.

    Bare ``str`` / ``bytes`` are excluded so JSON-string outputs in the
    ``ui.tsx`` pattern pass through unchanged.
    """
    if isinstance(value, (str, bytes)):
        return False
    if isinstance(value, (Node, Tag, TagList)):
        return True
    return hasattr(value, "tagify")


class reactive_output(Renderer["Node | Jsonifiable"]):
    """Reactive output for shinyreact.

    Accepts:

    * :class:`~shinyreact.Node` and any htmltools ``TagChild`` (``Tag``,
      ``TagList``, ``Tagifiable``) — walked into the JSON wire tree.
    * Any JSON-serializable value (``dict``, ``list``, ``str``, ``int``,
      ``float``, ``None``) — passed through unchanged for
      ``useShinyOutputValue()``.

    Dependencies harvested from a walked tree cannot reach ``<head>`` after
    the page has rendered; declare them up-front via
    ``ui_output(..., extra_deps=[...])`` or at the page level. A warning is
    emitted if a returned tree carries any.
    """

    async def transform(self, value: object) -> Jsonifiable:
        if _should_walk(value):
            payload, deps = serialize_ui(value)
            if deps:
                names = ", ".join(d.name for d in deps)
                warn(
                    f"shinyreact: '{self.output_id}' returned content carrying "
                    f"HTMLDependency objects ({names}) that cannot be injected "
                    "after the page has rendered. Declare them up-front via "
                    "ui_output(..., extra_deps=[...]) or at the page level.",
                    UserWarning,
                    stacklevel=2,
                )
            return payload
        return value  # type: ignore[return-value]

    def auto_output_ui(self) -> Tag:
        return ui_output(self.output_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pkg-py/tests/test_reactive_output.py -v`
Expected: PASS (11 tests).

- [ ] **Step 5: Run the full Python suite**

Run: `make py-check-tests`
Expected: PASS (no remaining references to `Spec`/`Element`).

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyreact/_reactive_output.py pkg-py/tests/test_reactive_output.py
git commit -m "feat(py): reactive_output walks Node/Tag trees, warns on render-time deps (#88)"
```

---

## Phase 3 — JS renderer

### Task 7: Discriminated-union TypeScript types

**Files:**
- Rewrite: `js/src/spec.ts`

- [ ] **Step 1: Rewrite `spec.ts`**

Replace the entire contents of `js/src/spec.ts` with:

```typescript
import type { ComponentType, ReactNode } from "react";

/**
 * A node in the wire tree. `type` is a closed discriminant; `name` carries the
 * component name (`react`) or DOM tag name (`tag`). Mirrors the Python walker
 * output in `pkg-py/src/shinyreact/_spec.py`.
 */
export interface ReactElement {
  type: "react";
  name: string;
  props: Record<string, unknown>;
  children?: Element[];
}

export interface TagElement {
  type: "tag";
  name: string;
  props: Record<string, unknown>;
  children?: Element[];
}

export interface TextElement {
  type: "text";
  value: string;
}

export interface HtmlElement {
  type: "html";
  html: string;
}

export type Element = ReactElement | TagElement | TextElement | HtmlElement;

/**
 * The root payload rendered into a `.shinyreact-output` element: a single
 * node, or several sibling nodes (e.g. a Python `TagList`).
 */
export type Spec = Element | Element[];

/**
 * Props passed to registered React components. They receive the raw `react`
 * element plus already-rendered `children`, and read `element.props`.
 */
export interface RegisteredComponentProps {
  element: ReactElement;
  children: ReactNode;
}

/**
 * Map of component name → React component. Populated by downstream packages
 * via `window.shinyreact.registerComponents()`.
 */
export type ComponentRegistry = Record<
  string,
  ComponentType<RegisteredComponentProps>
>;
```

- [ ] **Step 2: Verify it type-checks (renderer will be red until Task 8)**

Run: `cd js && npx tsc --noEmit`
Expected: errors only in `renderer.tsx` / `index.ts` (consumers of the old shape). `spec.ts` itself has no errors. This is expected; proceed to Task 8.

- [ ] **Step 3: Commit**

```bash
git add js/src/spec.ts
git commit -m "feat(js): discriminated-union Element wire types (#88)"
```

---

### Task 8: Renderer dispatches on `type`

**Files:**
- Rewrite: `js/src/renderer.tsx`
- Rewrite: `js/src/__tests__/renderer.test.tsx`

- [ ] **Step 1: Rewrite the renderer test**

Replace the entire contents of `js/src/__tests__/renderer.test.tsx` with:

```tsx
import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import React from "react";
import type { Spec } from "../spec";
import { registerComponents, _resetForTests } from "../registry";
import { ShinyreactRenderer } from "../renderer";

beforeEach(() => {
  _resetForTests();
});

describe("ShinyreactRenderer", () => {
  it("renders a tag node with translated props and text child", () => {
    const spec: Spec = {
      type: "tag",
      name: "div",
      props: { className: "hi" },
      children: [{ type: "text", value: "hello" }],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe('<div class="hi">hello</div>');
  });

  it("recursively renders nested tag children", () => {
    const spec: Spec = {
      type: "tag",
      name: "div",
      props: {},
      children: [
        { type: "tag", name: "span", props: {}, children: [{ type: "text", value: "one" }] },
        { type: "tag", name: "span", props: {}, children: [{ type: "text", value: "two" }] },
      ],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe("<div><span>one</span><span>two</span></div>");
  });

  it("renders a html node via dangerouslySetInnerHTML", () => {
    const spec: Spec = { type: "html", html: "<b>bold</b>" };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe("<span><b>bold</b></span>");
  });

  it("dispatches a react node to a registered component receiving { element, children }", () => {
    const Box = ({
      element,
      children,
    }: {
      element: { props: Record<string, unknown> };
      children: React.ReactNode;
    }) => <section data-label={element.props.label as string}>{children}</section>;
    registerComponents(null, { Box });

    const spec: Spec = {
      type: "react",
      name: "Box",
      props: { label: "outer" },
      children: [{ type: "tag", name: "span", props: {}, children: [{ type: "text", value: "inside" }] }],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe('<section data-label="outer"><span>inside</span></section>');
  });

  it("throws on an unknown registered component name", () => {
    const spec: Spec = { type: "react", name: "Missing", props: {}, children: [] };
    // React surfaces the thrown error during render.
    expect(() => render(<ShinyreactRenderer spec={spec} />)).toThrow(/Missing/);
  });

  it("renders an array payload as sibling nodes", () => {
    const spec: Spec = [
      { type: "tag", name: "span", props: {}, children: [{ type: "text", value: "a" }] },
      { type: "tag", name: "span", props: {}, children: [{ type: "text", value: "b" }] },
    ];
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe("<span>a</span><span>b</span>");
  });

  it("honors an explicit key in props without rendering it as an attribute", () => {
    const spec: Spec = {
      type: "tag",
      name: "div",
      props: { key: "k1", className: "x" },
      children: [],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    // `key` is consumed by React, not emitted as a DOM attribute.
    expect(container.innerHTML).toBe('<div class="x"></div>');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd js && npx vitest run src/__tests__/renderer.test.tsx`
Expected: FAIL — old renderer expects flat `{root, elements}`.

- [ ] **Step 3: Rewrite `renderer.tsx`**

Replace the entire contents of `js/src/renderer.tsx` with:

```tsx
import React, { type ReactNode } from "react";
import type { ComponentRegistry, Element, Spec } from "./spec";
import { getRegistry } from "./registry";

function renderNode(
  el: Element,
  fallbackKey: React.Key,
  registry: ComponentRegistry,
): ReactNode {
  switch (el.type) {
    case "text":
      return el.value;
    case "html":
      return React.createElement("span", {
        key: fallbackKey,
        dangerouslySetInnerHTML: { __html: el.html },
      });
    case "tag": {
      const key = (el.props.key as React.Key) ?? fallbackKey;
      const children = (el.children ?? []).map((c, i) =>
        renderNode(c, i, registry),
      );
      return React.createElement(el.name, { ...el.props, key }, ...children);
    }
    case "react": {
      const key = (el.props.key as React.Key) ?? fallbackKey;
      const children = (el.children ?? []).map((c, i) =>
        renderNode(c, i, registry),
      );
      const Registered = registry[el.name];
      if (!Registered) {
        throw new Error(
          `[shinyreact] Unknown component "${el.name}". Register it via ` +
            `window.shinyreact.registerComponents() before rendering.`,
        );
      }
      return React.createElement(Registered, { element: el, children, key });
    }
  }
}

interface ShinyreactRendererProps {
  spec: Spec;
}

/**
 * Walks a wire tree (single node or array of sibling nodes) and renders it as
 * a React tree. The registry is read at render time so components registered
 * before the render lands are picked up.
 */
function ShinyreactRenderer({ spec }: ShinyreactRendererProps) {
  const registry = getRegistry();
  const nodes = Array.isArray(spec) ? spec : [spec];
  return <>{nodes.map((n, i) => renderNode(n, i, registry))}</>;
}

export { ShinyreactRenderer };
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd js && npx vitest run src/__tests__/renderer.test.tsx`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add js/src/renderer.tsx js/src/__tests__/renderer.test.tsx
git commit -m "feat(js): renderer dispatches on type discriminant (#88)"
```

---

## Phase 4 — static `Node` delivery (inline spec)

### Task 9: Extract the React-root cache into `roots.ts`

**Files:**
- Create: `js/src/roots.ts`
- Modify: `js/src/index.ts`

- [ ] **Step 1: Create `roots.ts`**

Create `js/src/roots.ts`:

```typescript
import { createRoot, type Root } from "react-dom/client";

// One React root per output DOM element.
const roots = new WeakMap<Element, Root>();

export function getOrCreateRoot(el: HTMLElement): Root {
  let root = roots.get(el);
  if (!root) {
    root = createRoot(el);
    roots.set(el, root);
  }
  return root;
}

export function hasRoot(el: Element): boolean {
  return roots.has(el);
}

export function unmountRoot(el: Element): void {
  const root = roots.get(el);
  if (root) {
    root.unmount();
    roots.delete(el);
  }
}
```

- [ ] **Step 2: Rewrite the root cache usage in `index.ts`**

In `js/src/index.ts`, remove the local `roots` WeakMap and `getOrCreateRoot` function (lines defining `const roots = new WeakMap...` through the end of `getOrCreateRoot`), and add an import near the other imports:

```typescript
import { getOrCreateRoot, hasRoot, unmountRoot } from "./roots";
```

Then update `ShinyreactOutputBinding.renderValue` to use the shared helpers:

```typescript
  renderValue(el: Element, data: Spec | null): void {
    if (!data) {
      if (hasRoot(el)) unmountRoot(el);
      return;
    }
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(React.createElement(ShinyreactRenderer, { spec: data }));
  }
```

(`renderError` keeps calling `getOrCreateRoot` — now imported.)

- [ ] **Step 3: Type-check**

Run: `cd js && npx tsc --noEmit`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add js/src/roots.ts js/src/index.ts
git commit -m "refactor(js): extract shared React-root cache into roots.ts (#88)"
```

---

### Task 10: `seedInlineSpecs()` renders inline-spec scripts

**Files:**
- Create: `js/src/inline-spec.tsx`
- Create: `js/src/__tests__/inline-spec.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `js/src/__tests__/inline-spec.test.tsx`:

```tsx
import { describe, it, expect, beforeEach } from "vitest";
import { _resetForTests } from "../registry";
import { seedInlineSpecs } from "../inline-spec";

beforeEach(() => {
  _resetForTests();
  document.body.innerHTML = "";
});

function mountStatic(specJson: string): HTMLElement {
  const div = document.createElement("div");
  div.className = "shinyreact-static";
  const script = document.createElement("script");
  script.type = "application/json";
  script.textContent = specJson;
  div.appendChild(script);
  document.body.appendChild(div);
  return div;
}

describe("seedInlineSpecs", () => {
  it("renders the inline spec into its containing static mount", async () => {
    const div = mountStatic(
      JSON.stringify({
        type: "tag",
        name: "div",
        props: { className: "seeded" },
        children: [{ type: "text", value: "hi" }],
      }),
    );
    seedInlineSpecs();
    // React 19 renders synchronously enough for jsdom; flush a microtask.
    await Promise.resolve();
    expect(div.innerHTML).toBe('<div class="seeded">hi</div>');
  });

  it("ignores a static mount with no child JSON script", () => {
    const div = document.createElement("div");
    div.className = "shinyreact-static";
    document.body.appendChild(div);
    expect(() => seedInlineSpecs()).not.toThrow();
  });

  it("does not re-render a mount that already has a root", async () => {
    mountStatic(JSON.stringify({ type: "text", value: "first" }));
    seedInlineSpecs();
    await Promise.resolve();
    // Second call is a no-op because the element already has a React root.
    expect(() => seedInlineSpecs()).not.toThrow();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd js && npx vitest run src/__tests__/inline-spec.test.tsx`
Expected: FAIL — `../inline-spec` does not exist.

- [ ] **Step 3: Create `inline-spec.tsx`**

Create `js/src/inline-spec.tsx`:

```tsx
import React from "react";
import type { Spec } from "./spec";
import { ShinyreactRenderer } from "./renderer";
import { getOrCreateRoot, hasRoot } from "./roots";

/**
 * Render every `.shinyreact-static` mount from its child
 * `<script type="application/json">` payload.
 *
 * This is the delivery path for `Node` objects embedded directly in page
 * chrome (no server render function, no output id). The script is linked to
 * its mount by DOM adjacency (it is the div's child), so no id is needed.
 * Mounts that already have a React root are skipped, keeping the pass
 * idempotent.
 */
export function seedInlineSpecs(): void {
  const mounts = document.querySelectorAll<HTMLElement>(".shinyreact-static");
  mounts.forEach((el) => {
    if (hasRoot(el)) return;
    const script = el.querySelector<HTMLScriptElement>(
      ':scope > script[type="application/json"]',
    );
    if (!script) return;

    let spec: Spec;
    try {
      spec = JSON.parse(script.textContent || "null");
    } catch (err) {
      console.error("[shinyreact] failed to parse inline static spec:", err);
      return;
    }
    if (spec == null) return;

    const root = getOrCreateRoot(el);
    root.render(React.createElement(ShinyreactRenderer, { spec }));
  });
}

/**
 * Install `seedInlineSpecs` to run once the DOM is ready. Safe to call at
 * bundle load; runs immediately if the document is already parsed.
 */
export function installInlineSpecSeeding(): void {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", seedInlineSpecs);
  } else {
    seedInlineSpecs();
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd js && npx vitest run src/__tests__/inline-spec.test.tsx`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add js/src/inline-spec.tsx js/src/__tests__/inline-spec.test.tsx
git commit -m "feat(js): seed static Node specs from inline JSON scripts (#88)"
```

---

### Task 11: Install inline-spec seeding at bundle load

**Files:**
- Modify: `js/src/index.ts`

- [ ] **Step 1: Wire seeding into `index.ts`**

In `js/src/index.ts`, add to the imports:

```typescript
import { installInlineSpecSeeding } from "./inline-spec";
```

and add, immediately after the `Shiny.outputBindings.register(...)` line at the end of the file:

```typescript
// Render any static Node specs embedded in page chrome (inline JSON scripts).
installInlineSpecSeeding();
```

- [ ] **Step 2: Type-check and run all JS tests**

Run: `cd js && npx tsc --noEmit && npx vitest run`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add js/src/index.ts
git commit -m "feat(js): install inline-spec seeding at bundle load (#88)"
```

---

### Task 12: `Node.tagify()` emits mount div + inline-spec script

**Files:**
- Modify: `pkg-py/src/shinyreact/_spec.py`
- Create: `pkg-py/tests/test_tagify.py`

- [ ] **Step 1: Write the failing test**

Create `pkg-py/tests/test_tagify.py`:

```python
import json
import re

from htmltools import HTMLDependency, TagList
from shinyreact._spec import Node


def _render(node: Node) -> str:
    return str(TagList(node.tagify()))


def test_tagify_emits_static_mount_with_child_script():
    node = Node(type="Chart", props={"data": [1, 2]})
    html = _render(node)

    # A static mount div (distinct class) containing a JSON script.
    assert 'class="shinyreact-static"' in html
    script_m = re.search(
        r'<script type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert script_m, html
    payload = json.loads(script_m.group(1))
    assert payload == {
        "type": "react",
        "name": "Chart",
        "props": {"data": [1, 2]},
        "children": [],
    }


def test_tagify_mount_has_no_id_and_is_not_an_output():
    html = _render(Node(type="Chart"))
    assert "shinyreact-output" not in html
    # The static mount carries no id attribute.
    div_m = re.search(r"<div[^>]*>", html)
    assert div_m
    assert " id=" not in div_m.group(0)


def test_tagify_includes_harvested_dependency():
    dep = HTMLDependency(name="mydep", version="1.0", source={"subdir": "/tmp"})
    node = Node(type="Card", props={}, children=[dep, "hello"])
    deps = node.tagify().get_dependencies()
    names = {d.name for d in deps}
    # Both shinyreact's own dep and the harvested one are present.
    assert "shinyreact" in names
    assert "mydep" in names


def test_tagify_escapes_script_breakout():
    from htmltools import HTML

    node = Node(type="Card", props={}, children=[HTML("</script><script>x</script>")])
    html = _render(node)
    # The "<" of the embedded </script> is escaped, so it cannot close the
    # inline-spec <script> early.
    assert "</script><script>x" not in html
    assert "\\u003c/script>" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/test_tagify.py -v`
Expected: FAIL — `Node` has no `tagify` attribute.

- [ ] **Step 3: Add `serialize()` and `tagify()` to `_spec.py`**

In `pkg-py/src/shinyreact/_spec.py`, add `json` to the imports at the top:

```python
import json
```

Add these two methods to the `Node` dataclass (after `to_dict`):

```python
    def serialize(self) -> tuple[dict[str, Any], list[HTMLDependency]]:
        """Serialize to the wire tree plus harvested HTML dependencies."""
        deps: list[HTMLDependency] = []
        return self._to_wire(deps), deps

    def tagify(self) -> TagList:
        """Render as a static `.shinyreact-static` mount carrying its spec.

        Makes ``Node`` a ``Tagifiable`` so it can be embedded directly in page
        chrome (e.g. ``page_react(tags.div(Node(...)))``). The mount has no id
        and is not a Shiny output; the JS bundle seeds it from the child script
        at load time. The inline JSON is linked to its mount by DOM adjacency.
        """
        from htmltools import tags

        from ._output import _dep

        node, deps = self.serialize()
        # Escape "<" as \\u003c (still valid JSON, parses back to "<" on the
        # client) so a payload containing "</script>" cannot break out of the
        # script element.
        spec_json = json.dumps(node).replace("<", "\\u003c")
        return TagList(
            _dep(),
            *deps,
            tags.div(
                tags.script(spec_json, type="application/json"),
                class_="shinyreact-static",
            ),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest pkg-py/tests/test_tagify.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the full Python suite**

Run: `make py-check-tests`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyreact/_spec.py pkg-py/tests/test_tagify.py
git commit -m "feat(py): Node.tagify() emits mount div + inline spec script (#88)"
```

---

## Phase 5 — build, example, docs

### Task 13: Rebuild and copy the JS bundle

**Files:**
- Modify: `js/dist/*`, `pkg-py/src/shinyreact/www/*` (generated)

- [ ] **Step 1: Build and copy**

Run: `make update-dist`
Expected: Builds `js/dist/shinyreact.js` and copies into `pkg-py/src/shinyreact/www/` (and `pkg-r/inst/lib/shiny/`).

- [ ] **Step 2: Confirm JS lint/tests still pass**

Run: `make js-lint && cd js && npx vitest run`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add js/dist pkg-py/src/shinyreact/www pkg-r/inst/lib/shiny
git commit -m "build: rebuild dist with tree wire format + inline seeding (#88)"
```

---

### Task 14: End-to-end Playwright test for interleaving

**Files:**
- Create: `pkg-py/tests/playwright/apps/nesting_app.py`
- Create: `pkg-py/tests/playwright/test_nesting.py`

Read `.claude/references/playwright-e2e-tests.md` before writing — it documents the fixture-app layout and the four traps. Follow the existing tests in `pkg-py/tests/playwright/` for the exact fixture/assertion conventions; the code below adapts those patterns.

- [ ] **Step 1: Create the fixture app**

Create `pkg-py/tests/playwright/apps/nesting_app.py`:

```python
"""Fixture app: interleaved htmltools + Node content, two delivery paths.

- A STATIC Node embedded in page chrome (delivered via inline script).
- A REACTIVE Node returned from @reactive_output (delivered via WebSocket),
  whose tree mixes htmltools tags, text, and a registered component.
"""

from pathlib import Path

import shinyreact
from htmltools import HTMLDependency, tags
from shiny import App, Inputs, Outputs, Session, reactive

_src_dir = Path(__file__).parent
_dep = HTMLDependency(
    name="nesting-fixture",
    version="1",
    source={"subdir": str(_src_dir)},
    script={"src": "nesting_fixture.js", "defer": ""},
)

app_ui = shinyreact.page_react(
    _dep,
    tags.div(
        tags.h1("Static chrome"),
        # Static Node embedded directly in htmltools chrome:
        shinyreact.Node("Badge", {"text": "static-badge"}),
        id="chrome",
    ),
    shinyreact.ui_output("reactive_card"),
)


def server(input: Inputs, output: Outputs, session: Session) -> None:
    @shinyreact.reactive_output
    def reactive_card():
        return shinyreact.Node(
            "Card",
            {"title": "Reactive"},
            children=[
                tags.div(
                    tags.span("mixed ", class_="label"),
                    shinyreact.Node("Badge", {"text": "nested-badge"}),
                ),
            ],
        )


app = App(app_ui, server)
```

- [ ] **Step 2: Create the fixture JS**

Create `pkg-py/tests/playwright/apps/nesting_fixture.js`:

```javascript
const { registerComponents, React } = window.shinyreact;

function Badge({ element }) {
  return React.createElement(
    "span",
    { className: "badge", "data-testid": "badge" },
    element.props.text,
  );
}

function Card({ element, children }) {
  return React.createElement(
    "section",
    { className: "card", "data-testid": "card" },
    React.createElement("h2", null, element.props.title),
    children,
  );
}

registerComponents(null, { Badge, Card });
```

- [ ] **Step 3: Write the e2e test**

Create `pkg-py/tests/playwright/test_nesting.py`:

```python
from pathlib import Path

from playwright.sync_api import Page, expect

from .conftest import ShinyAppProc  # match the import style of sibling tests

APP = Path(__file__).parent / "apps" / "nesting_app.py"


def test_static_node_seeds_from_inline_script(page: Page, run_app) -> None:
    proc = run_app(APP)
    page.goto(proc.url)
    # Static badge rendered from the inline <script> (no server output).
    badge = page.locator('#chrome [data-testid="badge"]')
    expect(badge).to_have_text("static-badge")


def test_reactive_tree_interleaves_tags_and_components(page: Page, run_app) -> None:
    proc = run_app(APP)
    page.goto(proc.url)
    card = page.locator('[data-testid="card"]')
    expect(card.locator("h2")).to_have_text("Reactive")
    expect(card.locator(".label")).to_have_text("mixed ")
    expect(card.locator('[data-testid="badge"]')).to_have_text("nested-badge")
```

> **Note for the implementer:** the `run_app`/`page` fixtures and `ShinyAppProc` import path must match whatever the existing Playwright suite uses. Open one passing test in `pkg-py/tests/playwright/` and copy its fixture wiring verbatim — do not invent fixture names. Adjust the import and fixture usage above to match.

- [ ] **Step 4: Run the e2e test**

Run: `make py-test-e2e`
Expected: PASS for `test_nesting.py` (both tests). If fixtures differ, align with the sibling tests and re-run.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/tests/playwright/apps/nesting_app.py pkg-py/tests/playwright/apps/nesting_fixture.js pkg-py/tests/playwright/test_nesting.py
git commit -m "test(e2e): interleaved static + reactive nesting (#88)"
```

---

### Task 15: Example app + docs

**Files:**
- Create: `examples/app-py/14-nesting/app.py`
- Create: `examples/app-py/14-nesting/nesting.js`
- Modify: `docs/features.md`
- Modify: `docs/todos.md`

- [ ] **Step 1: Create the example app**

Create `examples/app-py/14-nesting/app.py`:

```python
"""14-nesting: htmltools and React components interleaved in one tree.

Demonstrates "layer all the way down": htmltools `tags.*` and shinyreact
`Node`s nest inside each other at arbitrary depth, in both the static
page-chrome path and a reactive @reactive_output.
"""

from pathlib import Path

import shinyreact
from htmltools import HTMLDependency, tags
from shiny import App, Inputs, Outputs, Session

_src_dir = Path(__file__).parent
_dep = HTMLDependency(
    name="nesting-example",
    version=str(int((_src_dir / "nesting.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "nesting.js", "defer": ""},
)

app_ui = shinyreact.page_react(
    _dep,
    tags.div(
        tags.h1("Nesting demo"),
        # A React component embedded directly in htmltools chrome.
        shinyreact.Node("Badge", {"text": "I am a React component in chrome"}),
        tags.p("…and this is plain htmltools text."),
    ),
    shinyreact.ui_output("card"),
)


def server(input: Inputs, output: Outputs, session: Session) -> None:
    @shinyreact.reactive_output
    def card():
        return shinyreact.Node(
            "Card",
            {"title": "Mixed content"},
            children=[
                tags.div(
                    tags.strong("htmltools "),
                    "wrapping ",
                    shinyreact.Node("Badge", {"text": "a nested React badge"}),
                ),
            ],
        )


app = App(app_ui, server)
```

- [ ] **Step 2: Create the example JS**

Create `examples/app-py/14-nesting/nesting.js`:

```javascript
const { registerComponents, React } = window.shinyreact;

function Badge({ element }) {
  return React.createElement(
    "span",
    { style: { background: "#eef", borderRadius: "6px", padding: "2px 8px" } },
    element.props.text,
  );
}

function Card({ element, children }) {
  return React.createElement(
    "section",
    { style: { border: "1px solid #ccc", borderRadius: "8px", padding: "12px" } },
    React.createElement("h2", null, element.props.title),
    children,
  );
}

registerComponents(null, { Badge, Card });
```

- [ ] **Step 3: Smoke-test the example**

Run: `uv run shiny run examples/app-py/14-nesting/app.py --port 8000` (start), open `http://localhost:8000`, confirm the chrome badge, the paragraph, and the reactive card with a nested badge render; then stop the server.
Expected: all three render; no console errors.

- [ ] **Step 4: Update `docs/features.md`**

Add a row/entry under the app.py-pattern feature list describing nesting. Insert this bullet in the appropriate section (search for the `Node` / `reactive_output` entries and add alongside):

```markdown
- **Interleaved htmltools + React content** — `Node` is a `Tagifiable`; htmltools
  `tags.*`/`HTML`/strings and `Node`s nest at arbitrary depth in one tree.
  Serialized to a discriminated-union wire format (`react` | `tag` | `text` |
  `html`); HTML dependencies are harvested in the same traversal. Static `Node`s
  in page chrome are delivered via an inline `<script type="application/json">`.
  See `examples/app-py/14-nesting`.
```

- [ ] **Step 5: Update `docs/todos.md`**

Remove the "Can dynamic UI be supported? ..." TODO entry (the part asking whether render output can mix raw HTML / Shiny UI with components is now answered by this feature). If the entry covers other unresolved questions, trim only the now-answered portion and leave the rest, linking to the spec.

- [ ] **Step 6: Commit**

```bash
git add examples/app-py/14-nesting docs/features.md docs/todos.md
git commit -m "docs: nesting example + features entry; trim answered TODO (#88)"
```

---

### Task 16: Record the #69 re-parenting follow-up

**Files:**
- Modify: `docs/todos.md`

- [ ] **Step 1: Add the follow-up entry**

Add to `docs/todos.md` (under an appropriate heading):

```markdown
## Re-parent `Node` onto `UiReact(UiComponent, AllowsChildren)` (after #69)

`Node` is currently a standalone `Tagifiable` dataclass (see
`docs/superpowers/specs/2026-05-29-htmltools-spec-nesting-design.md`). Once #69
lands the `UiComponent` / `AllowsChildren` hierarchy, re-categorize `Node` as
`UiReact(UiComponent, AllowsChildren)`. This is cosmetic — it changes `Node`'s
base classes, not its `tagify()` / serialization behavior. Keep `Node`'s
`tagify()` and dependency surface aligned with what #69 expects of a
`UiComponent`.
```

- [ ] **Step 2: Commit**

```bash
git add docs/todos.md
git commit -m "docs: track #69 re-parenting of Node as follow-up (#88)"
```

---

## Phase 6 — full verification

### Task 17: Run the complete check suite

- [ ] **Step 1: Python checks**

Run: `make py-check`
Expected: format check + pyright + pytest all PASS.

- [ ] **Step 2: JS checks**

Run: `make js-lint && cd js && npx vitest run`
Expected: PASS.

- [ ] **Step 3: e2e**

Run: `make py-test-e2e`
Expected: PASS (including `test_nesting.py`).

- [ ] **Step 4: Confirm dist is in sync**

Run: `make update-dist && git status --porcelain js/dist pkg-py/src/shinyreact/www`
Expected: no changes (dist already committed in Task 13). If there are changes, commit them.

- [ ] **Step 5: Final commit (only if Step 4 produced changes)**

```bash
git add js/dist pkg-py/src/shinyreact/www pkg-r/inst/lib/shiny
git commit -m "build: sync dist (#88)"
```

---

## Self-Review Notes (for the planner; delete when executing)

- **Spec coverage:** §1 scope → Tasks 1,4,12 (interleaving both directions). §1 wire tree + §"closed discriminant" → Tasks 1,7,8. §2 full migration → Task 5. §3 walker rows + attr translation + dep harvest + runtime warn → Tasks 1–4, 6. §4 `Node`→`Tagifiable`/static delivery + transform disambiguation → Tasks 6, 9–12. §5 keys → Task 8 (explicit-key test). §6 renderer → Task 8. Testing section → Tasks 1–4, 6, 8, 10, 12, 14. Risks (`html` span, attr completeness, breaking removal, id collision) → covered by Tasks 8 (span test), 2 (attr), 5 (removal), 12 (unique ids).
- **Type consistency:** wire node keys `type`/`name`/`props`/`children`/`value`/`html` are identical across Python (`_walk`) and TS (`spec.ts`). `serialize_ui` returns `(payload, deps)`; `Node.serialize()` returns `(dict, deps)`; `Node.tagify()` uses `serialize()`. `getOrCreateRoot`/`hasRoot`/`unmountRoot` names match between `roots.ts`, `index.ts`, and `inline-spec.tsx`.
- **No placeholders:** every code/test step has full content. Task 14's fixture-wiring caveat is explicit (match sibling tests) rather than a placeholder.
