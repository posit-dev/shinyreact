# Class-based UI components

**Date:** 2026-05-20
**Status:** Proposal — for review by the Shiny team Friday 2026-05-29, then Joe / Winston / Andrew sign-off
**Scope:** `py-shiny` (not `shinyreact`)
**Related:**
- [`decisions/2026-05-20-stack-based-child-capture.md`](./2026-05-20-stack-based-child-capture.md) — a **separate, more contested** proposal that builds on this class hierarchy. The two are independent: classes can ship without it.
- [`decisions/2026-05-19-class-based-ui-type-system.md`](./2026-05-19-class-based-ui-type-system.md) — the "why bother with classes" benefits memo.
- `examples/app-py/14-unified-ui-prototype/` and `15-shinyui-with-blocks/` — the fuller `shinyui` vision (`.value()` / `.update()` accessors on instances).
- `examples/app-py/16-shinyuiclassonly-core/` and `17-shinyuiclassonly-express/` — the structure-only step proposed here.

> **Where this work lives today.** The two prototype packages (`shinyui`, `shinyuiclassonly`) and the four end-to-end examples (14–17) live in this `shinyreact` monorepo as the proof-of-concept playground. They are **independent of `shinyreact`** — none of these changes require React or the JSON-spec bridge. When the team approves the direction, the work moves to a `dev` branch on `posit-dev/py-shiny` for the actual implementation.

> **Two documents, two ideas.** This proposal covers **only** the class hierarchy and the accessors that hang off it. The question of *how children are captured* inside a `with` block — replacing Express's display-hook trick with an explicit stack — is a separate, more invasive proposal tracked in the sibling doc. Class-based UI works fine with today's capture mechanism; nothing here requires the stack change.

---

## TL;DR — for decision makers

We propose changing what a `py-shiny` UI component *is* — from a function that returns HTML to a class that records its arguments and renders later. Two stages:

1. **`ClassComponents`** — UI components become classes. Today `ui.card(...)` is a function that returns an `htmltools.Tag`. We change it to a class whose `__init__` records arguments and whose `tagify()` produces the `Tag` at render time. The call site looks identical; the change is in what the symbol *is*.
2. **`InstanceAccessors`** (door left open) — build `.value()` / `.update()` accessors on input/layout instances (the fuller `shinyui` vision in examples 14–15). Not in this proposal's required scope; technical questions are still open.

**This is additive.** Because each component instance still tagifies to the same `Tag`, classes are largely a drop-in replacement. They can ship incrementally, without a breaking-change release, and without committing to the stack-capture proposal in the sibling doc.

### Why now

- **One symbol per component, two call styles.** `card(...)` works as a function call (Core, positional children) and as a `with`-block (Express). Today we maintain two parallel surfaces for the same component.
- **Runtime type identity.** `isinstance(x, UiInput)` / `isinstance(x, UiLayout)` becomes a first-class, public check instead of string-matching on tag attrs or reaching into private classes.
- **Co-located metadata.** A component's factory, input handler, bookmark serializer, and update logic can live in one class instead of being spread across four files.
- **Decouple "what is rendered" from "how it is rendered."** Once components are classes that defer `tagify()`, the door opens to alternative renderers — React, raw HTML, JSON to a separate client — without changing user code. This is the long-term enabling step for things like `shinyreact`.
- **Better typing and discoverability.** IDE auto-complete on the right overload; `.value` / `.update` as methods rather than free floating functions.

### What it costs

- **A type-surface migration, not a behavioural one.** `ui.card(...)` returns a `card` instance instead of a `Tag`. Code that relies on the return being a literal `Tag` (rare, mostly internal) needs a `.tagify()` call. The vast majority of app code is unaffected.
- **Documentation pass.** The reference docs describe components as classes; signatures and `isinstance` semantics need to be documented. This is far smaller than a full v2 doc rewrite.
- **`InstanceAccessors` carries open design questions** (see below) — which is exactly why it is deferred and does not gate `ClassComponents`.

### Recommended path

- Land `ClassComponents` incrementally — it does not require a breaking release, and `shinyuiclassonly` already proves it works with today's capture mechanism.
- Defer `InstanceAccessors` to a follow-up once we have real per-session ergonomics to compare against. Its open syntax questions should not gate the structural change.
- Treat the [stack-capture proposal](./2026-05-20-stack-based-child-capture.md) as a fully separate decision. Classes do not depend on it.

---

## What we are asking decision makers to approve

1. The direction: **UI components become classes** in `py-shiny`, with a small, fixed inheritance lattice (`UiComponent` → `UiInput` / `UiOutput` / `UiLayout`, plus an `AllowsChildren` mixin).
2. That `ClassComponents` can land **additively / incrementally**, not gated on a breaking release.
3. That `InstanceAccessors` (`.value()` / `.update()` on instances) is **deferred** to a follow-up proposal.
4. The work plan: **a `dev` branch on `posit-dev/py-shiny`**, with the prototypes from this repo as the starting point.

A "no" answer means we keep UI components as function factories. A "yes to classes, defer accessors" answer is the recommended path.

---

## What changes for an app author

Almost nothing at the call site. The component is constructed the same way and renders the same HTML; it is now an instance of a class rather than the return of a factory function.

```python
from shiny import App, ui, render

app_ui = ui.page_fluid(
    ui.card(
        ui.markdown("Title"),
        ui.input_slider("n", "N", 1, 100, 10),
        ui.output_plot("plot"),
        id="main",
    )
)

def server(input, output, session):
    @render.plot
    def plot(): ...

app = App(app_ui, server)
```

`ui.card(...)` now returns a `card` instance. It tagifies to the same `Tag` it produces today, so `page_fluid` and `App` see no difference. New abilities the instance unlocks:

- `isinstance(c, ui.UiLayout)` — runtime type identity.
- (with `InstanceAccessors`, later) `slider.value()` to read, `card.update(...)` to push server-side changes.

The `with`-block / Express composition style is unchanged by *this* proposal — it continues to work through the existing capture mechanism. Whether to replace that mechanism is the [sibling doc's](./2026-05-20-stack-based-child-capture.md) question.

---

## Open questions called out for the team

These all concern `InstanceAccessors` (the deferred stage). They do **not** block `ClassComponents`.

- **How does an author read an input from a class instance?** The `shinyui` examples (14/15) propose `slider.value()` returning a reactive. Garrick floated `slider.value = 42` as a setter (Marimo-style). Joe-style concern: setter syntax hides reactivity. **Not resolved.** The class hierarchy works fine with the existing `input.<id>()` read pattern in the meantime.
- **Multiple input values per component** (plot click, hover, brush; data-frame selection): if `.value()` lands, what is the shape for a component with several? `value.click()` / `value.brush()` collected under a `value` namespace? Prefix all values, such as `value_click()`? **Not resolved.**
- **`Updatable` placement.** Is "can be updated from the server" a separate mixin, or always-present on `UiInput`? Most inputs are updatable, so folding it into `UiInput` is tempting; a few outputs (data frame) are also updatable, which argues for a mixin.

---

## Risks

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Too many classes → users confused about which to subclass | Medium | Medium | Keep the lattice small and fixed (`UiComponent` + three markers + one mixin). Document the decision tree. |
| Code relying on `ui.*` returning a literal `Tag` | Low | Low | Instances tagify on demand; add `.tagify()` at the few internal call sites that need a raw `Tag`. |
| `InstanceAccessors` drags on indefinitely | Medium | Low | Explicitly *not* gating `ClassComponents`. Ship classes first. |
| Typing complexity (`@overload`, reactive-returning methods) | Medium | Medium | Mirror the existing `@module` decorator's typing approach for `.value()`. |

---

## Timeline

- **2026-05-29 (Fri):** team review of this doc.
- **By 2026-06-02:** Joe / Winston / Andrew gut-check in Boston (in person, ~1–2 hours).
- **2026-06+:** prototype lift to `posit-dev/py-shiny@dev`. Standing review every two weeks.

---
---

# Technical details

This section is the implementation reference. Decision makers do not need to read past this line.

## `ClassComponents` — UI components as classes

### Class hierarchy

A small, fixed lattice:

```
UiComponent (ABC; tagify() -> Tag; html_dependencies ClassVar)
├── UiInput            (marker for "this provides an input value")
├── UiOutput           (marker for "this is a render target")
└── UiLayout           (marker for "this is structural")

AllowsChildren         (mixin: children: list[TagChild]; __enter__/__exit__)
```

- `UiComponent` is abstract. Subclasses **must** implement `tagify()`.
- `AllowsChildren` is a mixin used by anything that can contain children (cards, accordions, layouts). It owns the `__enter__` / `__exit__` protocol; inputs and outputs deliberately do not inherit from it, so `with ui.input_slider(...)` is a `TypeError`.
  - Maybe `UiLayout` adopts this functionality permanently? "Has children" is arguably the defining feature of a layout.
- The three markers (`UiInput`, `UiOutput`, `UiLayout`) carry no methods of their own under `ClassComponents`. They exist so downstream code can write `isinstance(c, UiInput)` against a stable, public surface (today this is private inside `shiny.ui`).

The `shinyuiclassonly` package in this repo is the reference implementation for `ClassComponents`. Per-component files own their `__init__` + `tagify()` in one place — the *"co-located metadata"* benefit from the [type-system memo](./2026-05-19-class-based-ui-type-system.md#3-co-located-metadata-per-component-structural-leveraged-by-ergonomics).

### Two call styles, one symbol

`@overload` on `__init__` gives both call styles a single class:

```python
class card(UiLayout, AllowsChildren):
    @overload
    def __init__(self, *children: TagChild, id: str | None = None,
                 full_screen: bool = False) -> None: ...
    @overload
    def __init__(self, *, id: str | None = None,
                 full_screen: bool = False) -> None: ...
    def __init__(self, *children, id=None, full_screen=False):
        self._id = id
        self._full_screen = full_screen
        super().__init__(*children)        # AllowsChildren stores children

    def tagify(self) -> Tag:
        # ... existing shiny.ui.card logic, just deferred
```

IDE auto-complete picks the overload by call form: `card(child1, child2)` vs `with card() as c:`.

The `__enter__` / `__exit__` protocol on `AllowsChildren` is what makes `with card():` legal syntactically. *How* children created inside that block get appended — via Express's display hook today, or via a construction-time stack later — is independent of the class hierarchy and is the subject of the [sibling proposal](./2026-05-20-stack-based-child-capture.md). The prototype's `AllowsChildren` already supports today's display-hook capture.

### Lazy `tagify()`

Today, `ui.card(...)` does the work of building a `Tag` immediately. With classes, `__init__` only records arguments — the `Tag` is constructed when an outer consumer calls `.tagify()`. The lazy-tagify property is what unlocks the broader benefits:

- Express layout components (e.g. `layout_column_wrap`) needed access to *children* at tagify time but the current factory pattern couldn't see them. With classes, tagify runs *after* the entire `with` block has populated `children`.
- Late binding of session-dependent details (HTML dependencies, role attrs, ARIA wiring) becomes natural — `tagify()` can consult the active session if one is in scope.
- Decoupling intent from rendering: alternative `tagify()`-equivalents (e.g. `to_react_spec()`, `to_json()`) can be added without touching user code. This is the long-term hook for `shinyreact` and similar.

## `InstanceAccessors` — `.value()` / `.update()` on instances (deferred)

Sketched fully in [`decisions/2026-05-19-class-based-ui-type-system.md`](./2026-05-19-class-based-ui-type-system.md) and examples 14–15. The structural change (`ClassComponents`) does not require it; it is the *ergonomic* layer on top.

The idea: an input instance carries a reactive read accessor and a server-side update method, so the data flow is visible at the component rather than via free functions.

```python
slider = ui.input_slider("n", "N", 1, 100, 10)

# read (reactive) — instead of input.n()
@render.text
def label():
    return f"n = {slider.value()}"

# update (server-side) — instead of ui.update_slider("n", value=50)
slider.update(value=50)
```

Open questions (also listed in the decision-maker section):

- Reading: `slider.value()` (reactive calc method, explicit) vs `slider.value` (property, implicit reactivity) vs Marimo-style `slider.value = 42` setter (Joe-style concern: hides reactivity).
- Multiple values per component: namespace them (`plot.value.click()`, `plot.value.brush()`) so they auto-complete together — or prefix individually (`plot.value_click()`, `plot.value_brush()`).
- Update method placement: `Updatable` as a separate mixin vs. always-present on `UiInput`.

These should be decided in a follow-up after `ClassComponents` is in place and we have real per-session ergonomics to compare against. `shinyui` (vs. `shinyuiclassonly`) is the prototype that carries this layer.

## Implementation notes

### Where the prototypes live today

| Package | Purpose | Notes |
|---|---|---|
| `pkg-py/src/shinyuiclassonly/` | `ClassComponents` reference: class hierarchy + `AllowsChildren` | Structure only — no session-bound accessors. This is the scope of *this* proposal. |
| `pkg-py/src/shinyui/` | `InstanceAccessors` reference: above + session-bound `.value()` / `.update()` / per-session id registry | Demonstrates the fuller vision; deferred stage. |
| `examples/app-py/14-unified-ui-prototype/` | `shinyui` in Core form | |
| `examples/app-py/15-shinyui-with-blocks/` | `shinyui` in Express `with`-block form | |
| `examples/app-py/16-shinyuiclassonly-core/` | `shinyuiclassonly` in Core form (this proposal's structural step) | |
| `examples/app-py/17-shinyuiclassonly-express/` | `shinyuiclassonly` in Express `with`-block form | |

### Files that change in `py-shiny`

Roughly:

- `shiny/ui/_*.py` — every component factory becomes a class (`UiInput`, `UiOutput`, or `UiLayout`+`AllowsChildren` subclass). `tagify()` keeps the old factory body verbatim.
- `shiny/ui/__init__.py` — export the base classes (`UiComponent`, `UiInput`, `UiOutput`, `UiLayout`, `AllowsChildren`) for `isinstance` use.
- (`InstanceAccessors`, later) `shiny/render/` and the input-handler / bookmark machinery move into per-component classes.

### `dev` branch strategy

- Branch: `dev` on `posit-dev/py-shiny`.
- Planning artifacts (this doc, follow-up specs) live in the branch under `docs/` or `decisions/` and are deleted before merge.
- Releases continue from `main`. `dev` is parallel and does not block ongoing releases.
- PRs into `dev` are how iteration happens; review checkpoints every two weeks.

### Non-goals for this proposal

- Stack-based child capture and unified Core/Express mode. Tracked in the [sibling doc](./2026-05-20-stack-based-child-capture.md); a separate, contested decision.
- React rendering / `shinyreact` integration. The "decouple intent from rendering" framing is the long-term enabling argument, but `shinyreact` continues with its current `ui.tsx` and JSON-spec approach independent of this work.
- R-package equivalent. Out of scope; revisit once the Python design stabilises.

---

## Appendix — meeting context

This proposal crystallises the class-hierarchy portion of the 2026-05-20 meeting with Barret, Carson, Liz, and Garrick. Key resolutions captured:

- UI classes are a good idea and are independent of the capture mechanism (all four). They can land first, on their own.
- Keep the class lattice small to avoid confusion about which class to subclass (Carson).
- `InstanceAccessors` is deferred (`slider.value()` vs `slider.value` is unresolved).
- Doc target: Friday 2026-05-29 for team review; Joe / Winston / Andrew sign-off in Boston.
