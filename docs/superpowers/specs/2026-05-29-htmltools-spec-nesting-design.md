# Layer all the way down: nesting htmltools and the React spec at arbitrary depth

**Date:** 2026-05-29
**Status:** Design — sub-issue of #68 (unified UI component class). **Independent of #69** for the serialization work itself: the capability needs only that `Node` implement `Tagifiable` (`.tagify()`). Categorizing `Node` as `UiReact(UiComponent, AllowsChildren)` is a small follow-up that lands when #69's hierarchy exists (see §4).
**Tracking issue:** #88
**Related:** #87 (HTMLDependency harvesting inside modules), #68/#69 (unified UI component class), #35/#36 (JSON Patch wire format — unimplemented; tree format is compatible).

## Summary

Today the boundary between regular htmltools content (`Tag`, `TagList`, `HTML`, strings) and shinyreact's React data model (`Spec`, `Element`, `Node`) is binary. The two worlds don't compose: you cannot put a `Tag` inside `Element.children`, and you cannot put a `Node` inside an htmltools tag's children. As soon as part of a UI needs the other side, you must escape — describe everything as React components (losing htmltools ergonomics and `HTMLDependency` injection) or move the whole subtree out of the spec.

This design makes a **single tree the source of truth**. A `Node` becomes a `TagChild` (`Tagifiable`), so htmltools content and React-component content interleave at any depth in either direction:

```python
Node("Card", {}, [
    tags.div(                              # regular htmltools
        tags.h2("Title"),
        Node("Chart", {"data": ...}),      # spec content nested inside an htmltools tag
        "raw text and ", tags.code("inline"),
    ),
    Node("Footer", {}, ["more spec children"]),
])
```

A single recursive walker (shaped like Shiny's `process_ui`) converts any mixed subtree into a JSON spec tree plus a harvested list of `HTMLDependency`. The walk runs in both directions because the tree is uniform — there is no longer a "spec side" and an "htmltools side," only nodes the walker knows how to convert.

## Goals

- Interleave htmltools `TagChild` and `Node`/`Element` content at arbitrary depth, in either direction.
- A `Node` is a first-class `TagChild` (`Tagifiable`) — it can sit anywhere htmltools content can.
- One traversal converts a mixed tree to `(spec_tree, html_dependencies)`.
- The wire format is a plain recursive tree (no flat element map, no synthetic keys).
- React reconciliation behaves like hand-written React (positional + explicit `key`).
- Coverage proves the walk in both directions and the two delivery paths.

## Non-goals

- Building the `UiComponent` hierarchy itself — that is #69, a separate and independent effort. This work needs only `Node.tagify()`, not the hierarchy.
- Solving runtime `HTMLDependency` delivery for deps discovered after page render — that is #87 / a future custom-message mechanism. This design extracts and *warns*; it does not retroactively inject.
- Changing how the `ui.tsx` pattern ships JSON data outputs (`useShinyOutputValue` payloads pass through unchanged).
- The R package equivalent (follow-up if the Python design proves out).

## Design

### 1. Wire format: flat map → recursive tree (discriminated union)

The flat `{root, elements: {key: …}}` representation is removed. The wire node is a single recursive shape whose `type` field is a **closed discriminant** — one of `react`, `tag`, `text`, `html` — never a user-supplied name. The specific identifier (component name or DOM tag name) lives in a separate `name` field:

```jsonc
{ "type": "react", "name": "Card", "props": { "title": "Hi" }, "children": [ /* … */ ] }  // registered React component
{ "type": "tag",   "name": "div",  "props": { "className": "card" }, "children": [ /* … */ ] }  // htmltools DOM element
{ "type": "text",  "value": "raw text" }                                                    // text leaf
{ "type": "html",  "html": "<b>…</b>" }                                                     // opaque raw HTML
```

- `children` is a **homogeneous `list[Element]`** — there is no `str` member in the union. Every child is an object dispatched by its `type`.
- `react` and `tag` **share one envelope** (`name` + `props` + `children`); they differ only in how `name` resolves — a registry lookup vs `React.createElement(name, …)` for an intrinsic DOM element. A registered component and a DOM tag are therefore structurally identical, distinguished solely by `type`.
- `text` carries its string in `value`; `html` carries pre-rendered markup in `html` and renders via `<span dangerouslySetInnerHTML>`. `html` is the single opaque fallback (used for `HTML(...)` / `markdown(...)` output). **Known limitation:** the `<span>` wrapper is invalid for block-level raw HTML; documented, revisitable (configurable wrapper tag) if it bites.

**Why a closed discriminant.** Overloading one `type` field with sentinels, component names, *and* DOM tag names forces the renderer to probe the registry to learn what a node is, and invites collisions — a component named `div`, or an `<input type="text" name="email">` whose tag, attributes, and node-kind all compete for the words "type"/"name". A closed `type` plus a separate `name` removes both: the renderer dispatches on a four-value enum, and component/tag identifiers never collide with the discriminant or with each other's attributes (tag name lives at `name`; the HTML `name=`/`type=` attributes live inside `props`).

### 2. Full migration of the public spec surface (option i)

- Remove the flat `Spec` class and `Node.to_spec()` / `auto_NNN` key assignment.
- `Node.to_dict()` recurses directly to the tree format. `Element` is the tree node (gains nested `children: list[Element]`).
- Rewrite `pkg-py/tests/test_spec.py` and `pkg-py/tests/test_reactive_output.py` to the tree format. No example app uses the flat `Spec` directly (verified: `examples/ui-tsx/04-shadcn` and `03-columns-shadcn` only reference React DOM `createRoot`, unrelated).
- `Spec` is pre-1.0 and the #68 design explicitly sanctions cheap breaking changes here. Default is a clean removal; a short-lived deprecation alias for `Spec` is acceptable if a soft landing is wanted.

### 3. The walker (`process_ui`-shaped)

One recursive traversal converts any mixed `TagChild` subtree into `(Element_tree, list[HTMLDependency])`:

| Input node | Treatment |
|---|---|
| `Tag` | Emit `{type: "tag", name: tag.name, props: translatedAttrs, children: […]}`; recurse into children. |
| `TagList` | Flatten transparently into the parent's children. |
| `str` / `int` / `float` / `bool` | `{type: "text", value: str(x)}`. |
| `HTML(...)` | `{type: "html", html: str(x)}`. |
| `None` | Skipped (htmltools convention). |
| `HTMLDependency` / other `MetadataNode` | **Not** a tree node — collected into the dep side-list. |
| `Node` (a `UiReact`) | Emit `{type: "react", name: …, props, children}`, folded into the same tree; its `html_dependencies` collected. |
| other `Tagifiable` / `UiComponent` | `.tagify()`, then recurse; deps collected. |

**Attribute translation.** htmltools has already normalized `class_`→`class`, `for_`→`for` etc. by the time we see `Tag.attrs`. The walker maps HTML attribute names to React props: `class`→`className`, `for`→`htmlFor`, camelCase the known set (`tabindex`→`tabIndex`, …); `data-*` and `aria-*` pass through verbatim. Event-handler attributes have no representation today and are dropped (htmltools tags don't carry React handlers).

**Worked example.** Input:

```python
tags.div(
    "hello ",
    tags.span("x", class_="hl"),
    Node("Chart", {"data": [1, 2]}),
    class_="card", id="c1",
)
```

walks to:

```jsonc
{
  "type": "tag", "name": "div",
  "props": { "className": "card", "id": "c1" },
  "children": [
    { "type": "text", "value": "hello " },
    { "type": "tag", "name": "span", "props": { "className": "hl" },
      "children": [ { "type": "text", "value": "x" } ] },
    { "type": "react", "name": "Chart", "props": { "data": [1, 2] }, "children": [] }
  ]
}
```

The `div`/`span` render as intrinsic React host elements (attributes translated to props); the `Node` resolves through the component registry — all one tree, reconciled by React normally.

**Dependency flow.** Harvested deps go to Shiny's normal `<head>` channel via the surrounding `ui_output` / `page_react` / `set_react_page` (the same path `ui_output(extra_deps=[...])` uses today).

**Runtime caveat.** A `Node` returned from `@reactive_output` ships over the WebSocket *after* the page has rendered, so harvested deps cannot retroactively reach `<head>`. The rule stays: declare deps up-front at `ui_output(extra_deps=…)` / page level. The walker still extracts them and **warns** when a render-time `Node` carries deps not already known to the page. Full runtime delivery is out of scope (#87 / future custom-message mechanism).

### 4. `Node` as `UiReact`; delivery of static `Node`s

The interleaving capability comes from one thing: **`Node` implements `Tagifiable`** (a `.tagify()` method), so it can sit anywhere an htmltools `TagChild` can. That is independent of #69 and is built now. `Node.tagify()` produces a `.shinyreact-output` mount point plus a JSON spec, not direct HTML.

When #69's hierarchy lands, `Node` is re-categorized as **`UiReact(UiComponent, AllowsChildren)`** — a new sibling category alongside `UiInput` / `UiOutput` / `UiLayout`. It is structurally distinct (its `tagify()` produces a mount point + spec, not HTML), and naming it its own category rather than reusing `UiLayout` prevents the conceptual drift of "a layout that isn't really a layout." This re-parenting is cosmetic — it changes `Node`'s base classes, not its serialization behavior — and is tracked as a follow-up task, not a blocker for this work.

**Authoring API unchanged (decision (a)).** Users keep writing `Node(type="Card", props=…, children=…)`; `to_dict()` maps `self.type` → the wire `name` field and stamps `type: "react"`. The Python constructor param keeps the name `type` even though it lands in the wire `name` field — a contained mismatch internal to `to_dict()`, with zero churn to the many existing `Node(type=…)` call sites. A rename to `Node(name=…)` is deferred to (and decided within) the #69 `UiReact` work.

**Two delivery contexts, one folding rule.** The recursion always converts a mixed subtree into *one* spec tree. Only the delivery differs:

- **Inside `@reactive_output`** returning a `Node` / mixed tree → the whole subtree folds into one spec and ships over the WebSocket, exactly as today. Nested `Tag`s and nested `Node`s are all folded in.
- **Static `Node` in page chrome** (e.g. `page_react(tags.div(Node("Chart", …)))`, no render function feeding it) → `tagify()` emits a self-contained mount carrying its spec as a child script:

  ```html
  <div class="shinyreact-static">
    <script type="application/json">{…tree…}</script>
  </div>
  ```

  **No id.** A static `Node` is not a Shiny output, so it gets no output id — honoring "ids are required for *outputs*" by simply not pretending a static node is one. The inline script is linked to its mount by **DOM adjacency** (it's the div's child), not by an id reference. A separate `.shinyreact-static` class keeps these mounts out of the output binding's `find()` (`.shinyreact-output`), so Shiny never tries to bind an id-less output. The JS seeding pass finds each `.shinyreact-static`, parses its child script, and renders the tree into the div. The serialized JSON escapes `<` as `<` (still valid JSON, parses back to `<` on the client) so a payload containing `</script>` cannot break out of the script element.

  Outputs and static nodes are therefore fully separated: outputs (`.shinyreact-output`, id required) are WebSocket-fed; static nodes (`.shinyreact-static`, no id) are inline-only. There is no hybrid path.

  "Static" describes only the spec *shape* — interior React components still subscribe to inputs/outputs reactively (`useShinyInputValue`, etc.) at runtime.

**`reactive_output.transform` disambiguation.** Walk when the value is `Node` / `Tag` / `TagList` / `Tagifiable`; **pass through unchanged** for bare `str` / `int` / `dict` / `list` (preserves `ui.tsx` apps whose outputs are JSON strings consumed by `useShinyOutputValue`). A `str`→`text`-node conversion happens **only** for a string encountered as a *child* during walking — never for a top-level return value.

### 5. Keys

Converting the wire to a tree dissolves the auto-key churn problem the issue raised: there are no synthetic map keys to renumber when a subtree changes shape. Reconciliation falls back to React's native behavior — positional by default, with an explicit `key` (carried in `props`, read natively by React) for lists / reorderable content. This is the mental model React developers already have; nothing custom is built or taught. The previous positional `auto_NNN` counter (which churned everything after an insertion point) is gone with the flat format.

### 6. JS renderer

`renderNode` in `js/src/renderer.tsx` changes from flat-map-lookup recursion to direct child recursion over `el.children`, dispatching on the closed `type` discriminant:

- `react` → `registry[el.name]`; **unknown name → error** (catches typos; replaces today's silent intrinsic fallback).
- `tag` → `React.createElement(el.name, props, ...children)` (intrinsic DOM element).
- `text` → `el.value` (React renders the string as a text node).
- `html` → `React.createElement("span", {dangerouslySetInnerHTML: {__html: el.html}})`.

`js/src/spec.ts` `Element` becomes a discriminated union (`type: "react" | "tag" | "text" | "html"`, with `name`/`props`/`children` present on `react` and `tag`); the flat `Spec` interface is removed (or aliased) to match the Python migration.

## Testing

Bug-fix-grade coverage (per repo testing policy):

- **Python walker unit tests** — one per dispatch row (`Tag` → `tag`, `TagList` flatten, str/numeric → `text`, `HTML` → `html`, `None` skip, `HTMLDependency`/metadata → side-list, `Node` → `react` fold, `Tagifiable`/`UiComponent` tagify+recurse); attribute translation (`class`→`className`, `for`→`htmlFor`, `data-*`/`aria-*` passthrough); nested `Node`-in-`Tag`-in-`Node` folds into one tree; dependency harvesting from a deep mixed tree; an `<input type="text" name="email">` round-trip proving tag name vs `type=`/`name=` attributes don't collide.
- **`reactive_output` disambiguation tests** — top-level `str`/`dict`/`list` passes through as JSON; child `str` becomes a `text` node; render-time `Node` carrying unknown deps emits a warning.
- **Rewrites** — `pkg-py/tests/test_spec.py`, `pkg-py/tests/test_reactive_output.py` to the tree format.
- **JS vitest** — renderer dispatch per `type`: `text`, `html`, `react` (registry hit + unknown-name error), `tag` (intrinsic), nested mix; explicit `key` honored.
- **Playwright e2e** — (a) static `Node` in page chrome seeds from the inline `<script>` (no WebSocket value), (b) a reactive mixed tree returned from `@reactive_output` renders htmltools + components interleaved.

## Risks

- **#69 re-categorization drift.** This work makes `Node` a `Tagifiable`; #69 later re-parents it onto `UiReact(UiComponent, AllowsChildren)`. The two could drift (e.g. #69 expects a method/attribute this `Node` doesn't expose). Mitigation: the re-parenting is a tracked follow-up and is cosmetic (base classes only); keep `Node`'s `tagify()` / `html_dependencies` surface aligned with what the #69 spec expects of a `UiComponent`.
- **`html` node span wrapper.** Invalid for block-level raw HTML. Mitigation: document; add a configurable wrapper tag if a real case appears.
- **Attribute-translation completeness.** The HTML-attr → React-prop map is a known but open-ended set. Mitigation: cover the common attributes, pass `data-*`/`aria-*` through, and treat unknown attributes as pass-through; expand the map as gaps surface.
- **Breaking removal of flat `Spec`.** External code we can't see may import `shinyreact.Spec`. Mitigation: pre-1.0 status sanctions the break; offer a short-lived deprecation alias if wanted.
- **Static-Node double-mounting.** A static mount must not be picked up by both the output binding and the seeding pass. Mitigation: static mounts use a distinct `.shinyreact-static` class (not `.shinyreact-output`) and carry no id, so the output binding's `find()` never matches them; the seeding pass is their only renderer. The shared root cache (`hasRoot`) keeps the seeding pass idempotent.

## What this spec does not commit to

- Runtime `HTMLDependency` delivery for deps discovered after first render (#87 territory).
- The exact contents of the attribute-translation map beyond the common set named above.
- A PR landing order relative to the other #68 sub-issues (sequenced when scheduled; only the #69 dependency is firm).
