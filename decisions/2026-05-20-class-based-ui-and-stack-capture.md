# Class-based UI components and stack-based child capture

**Date:** 2026-05-20
**Status:** Proposal — for review by the Shiny team Friday 2026-05-29, then Joe / Winston / Andrew sign-off
**Scope:** `py-shiny` (not `shinyreact`)
**Branch plan:** prototype in a `dev` branch on `posit-dev/py-shiny`; targets a **Shiny v2 / breaking** release
**Related:**
- [`decisions/2026-05-19-class-based-ui-type-system.md`](./2026-05-19-class-based-ui-type-system.md) — the "why bother with classes" benefits memo.
- `examples/app-py/14-unified-ui-prototype/` and `15-shinyui-with-blocks/` — the fuller `shinyui` vision (`.value()` / `.update()` accessors on instances).
- `examples/app-py/16-shinyuiclassonly-core/` and `17-shinyuiclassonly-express/` — the structure-only step proposed here.

> **Where this work lives today.** The two prototype packages (`shinyui`, `shinyuiclassonly`) and the four end-to-end examples (14–17) live in this `shinyreact` monorepo as the proof-of-concept playground. They are **independent of `shinyreact`** — none of these changes require React or the JSON-spec bridge. When the team approves the direction, the work moves to a `dev` branch on `posit-dev/py-shiny` for the actual implementation.

---

## TL;DR — for decision makers

We are proposing five staged changes to how `py-shiny` defines UI. The names describe what the step does; numbering is implementation order:

1. **`ClassComponents`** — UI components become classes. Today `ui.card(...)` is a function that returns an `htmltools.Tag`. We change it to a class whose `__init__` records arguments and whose `tagify()` produces the `Tag` at render time. The call site looks identical; the change is in what the symbol *is*.
2. **`StackCapture`** — replace Express's "print to capture" trick with an explicit stack. Express today uses Python's display hook (`sys.displayhook`) to detect that a UI element was created at the top of a `with` block and stitch it into the parent. We replace that with an explicit push/pop context stack maintained by the class. The class captures children when it is constructed inside a `with` block.
3. **`HtmlToolsStack`** — push the stack primitive down into `htmltools` once `StackCapture` is in. Plain `htmltools.tags.div(...)` participates in the same stack, so the mechanism is shared between Shiny and any other consumer of `htmltools`.
4. **`UnifiedMode`** — collapse "Core mode" and "Express mode" into one mode. Once child capture is explicit, the two runtimes converge: the same app file works whether or not a `server` function is present, with `with global_session():` as the opt-in for declarations that should *not* be session-scoped.
5. **`InstanceAccessors`** (door left open) — build `.value()` / `.update()` accessors on input/layout instances (the fuller `shinyui` vision in examples 14–15). Not in this proposal's required scope; technical questions are still open.

### Why now

- **One symbol per component, two call styles.** `card(...)` works as a function call in Core and as a `with`-block in Express. Today we maintain two parallel surfaces.
- **Context managers in Core.** Authors get the nested-`with` style they like in Express without committing to Express's display-hook semantics.
- **Decouple "what is rendered" from "how it is rendered."** Once components are classes that defer `tagify()`, the door opens to alternative renderers — React, raw HTML, JSON to a separate client — without changing user code. This is the long-term enabling step for things like `shinyreact`.
- **Better typing and discoverability.** `isinstance(x, UiInput)`, IDE auto-complete on the right overload, `.value` / `.update` as methods rather than free floating functions.

### What it costs

- **Shiny v2.** `StackCapture` is a breaking change to Express: every UI element placed at the top of a `with` block must be a recognised component. Bare literals (`42`, `"text"`) and unwrapped raw values no longer render. Migration is mechanical (wrap in `ui.markdown(...)` or similar) but pervasive.
- **Documentation overhaul.** The website, tutorials, and examples need a re-pass to reflect the unified mental model.
- **Notebook-render behaviour to validate.** Display hooks are used by Jupyter/IPython for rich output. The stack approach needs an explicit story for "I'm in a notebook, top-level objects should still render."

### Recommended path

- Land `ClassComponents` and `StackCapture` together in the `dev` branch. They are mutually reinforcing and both are required to unlock the Express simplification.
- Land `HtmlToolsStack` immediately after `StackCapture` is stable.
- Land `UnifiedMode` as a follow-up, once team and users are comfortable with the new model.
- Defer `InstanceAccessors` to a separate proposal — the structural change stands on its own merits and `InstanceAccessors` has open syntax questions that should not gate the rest.

---

## What we are asking decision makers to approve

1. The direction: **classes + stack capture as the single way to compose UI in Shiny v2**.
2. The breaking-change commitment: **Express mode requires all rendered top-level values to be wrapped components** post-v2.
3. The staging order: **`ClassComponents` + `StackCapture` together, then `HtmlToolsStack`, then `UnifiedMode`, then `InstanceAccessors`**.
4. The work plan: **a `dev` branch on `posit-dev/py-shiny`**, with the prototypes from this repo as the starting point.
5. A standing review cadence (every two weeks) until v2 ships.

A "no" answer at this point means we stop the prototype line and continue to maintain Core + Express as two surfaces. A "yes, but stage `UnifiedMode` / `InstanceAccessors` later" answer is fully supported by the proposal.

---

## What changes for an app author

### Today (Shiny 1.x)

```python
# Core
from shiny import App, ui, render, reactive

app_ui = ui.page_fluid(
    ui.card(
        "Title",
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

```python
# Express — same UI, different runtime, different idiom
from shiny.express import ui, render, input

with ui.card(id="main"):
    "Title"
    ui.input_slider("n", "N", 1, 100, 10)

    @render.plot
    def plot(): ...
```

Two surfaces, two mental models. Express mode renders a top-level `ui.input_slider(...)` only because Python's display hook is hijacked.

### Under this proposal (Shiny v2)

```python
# One file, one set of imports. Works in both styles.
from shiny import App, ui, render, reactive

with ui.card(id="main") as main:
    ui.markdown("title"),
    ui.input_slider("n", "N", 1, 100, 10)
    ui.output_plot("plot")

# Core: keep an explicit server function.
def server(input, output, session): ...

app = App(main, server)
```

Or, when `UnifiedMode` lands:

```python
# No server function — session-scoped by default.
from shiny import ui, render

with ui.card(id="main") as main:
    ui.markdown("title")
    ui.input_slider("n", "N", 1, 100, 10)

    @render.plot
    def plot(): ...

app = App(main)   # session-lazy under the hood
```

### Migration in one sentence

Wrap top-level bare values in a component (`ui.markdown("text")`, etc.); everything else stays the same.

---

## Open questions called out for the team

- **How does an author read an input from a class instance?** The `shinyui` examples (14/15) propose `slider.value()` returning a reactive. Garrick floated `slider.value = 42` as a setter (Marimo-style). Joe-style concern: setter syntax hides reactivity. **Not resolved.** `InstanceAccessors` is gated on this. The proposal here works fine with the existing `input.<id>()` read pattern in the meantime.
- **Multiple input values per component** (plot click, hover, brush; data-frame selection): if `.value()` lands, what is the shape for a component with several? `value.click()` / `value.brush()` collected under a `value` namespace? Prefix all values, such as `value_click()`? **Not resolved.**
- **Notebook display hook.** Shiny shares the `sys.displayhook` mechanism with Jupyter. The stack approach must not break notebook rendering; one possibility is "print only when stack depth is zero." **Needs prototype validation.**
- **`auto_page` in Express.** Today Express's "auto-page" wrapping inspects what was displayed at the top level to decide between `page_fluid` / `page_sidebar` / `page_navbar`. Under the stack model, this becomes explicit (`App(main_layout)`) — confirming this is acceptable to users is part of the v2 messaging.
- **Reactives declared inside a `with` block.** A `@reactive.calc` inside a `with ui.card():` block should still be a function (Joe's "explicit reactivity" principle); under the unified mode we want it to be session-lazy so it can be defined once and resolved per session. **Solvable; needs spec.**

---

## Risks

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Migration noise for existing Express apps | High | Medium | Mechanical fix; clear error messages; codemod script if needed. |
| Notebook rendering regressions | Medium | High | Step-zero spike: validate display-hook behaviour against Jupyter, Quarto, VS Code interactive. |
| Documentation debt blocks v2 release | High | Medium | Liz involved from day one; doc rewrite tracked as a parallel workstream. |
| `InstanceAccessors` drags on indefinitely | Medium | Low | Explicitly *not* a v2 blocker. Ship the first four steps first. |
| Authors confused by "where does this render?" | Medium | Medium | Stack rule is simple: "constructed inside a `with` → goes into that parent; else → top level." Document with a flowchart. |

---

## Timeline

- **2026-05-29 (Fri):** team review of this doc.
- **By 2026-06-02:** Joe / Winston / Andrew gut-check in Boston (in person, ~1–2 hours).
- **2026-06+:** prototype lift to `posit-dev/py-shiny@dev`. Standing review every two weeks.
- **Shiny v2 release:** date deliberately not committed here; depends on doc rewrite and v2 messaging plan.

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
  - Maybe `UiLayout` adopts this functionality permanently?
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

### Lazy `tagify()`

Today, `ui.card(...)` does the work of building a `Tag` immediately. With classes, `__init__` only records arguments — the `Tag` is constructed when an outer consumer calls `.tagify()`. The lazy-tagify property is what makes the rest of this proposal possible:

- Express layout components (e.g. `layout_column_wrap`) needed access to *children* at tagify time but the current factory pattern couldn't see them. With classes, tagify runs *after* the entire `with` block has populated `children`.
- Late binding of session-dependent details (HTML dependencies, role attrs, ARIA wiring) becomes natural — `tagify()` can consult the active session if one is in scope.
- Decoupling intent from rendering: alternative `tagify()`-equivalents (e.g. `to_react_spec()`, `to_json()`) can be added without touching user code. This is the long-term hook for `shinyreact` and similar.

## `StackCapture` — stack-based child capture

### What we are replacing

Express today routes a top-level expression to its parent via:

```python
# Roughly: shiny.express._recall_capture
sys.displayhook = my_handler
with ui.card():
    ui.input_slider(...)   # printed → display hook → appended to card.children
```

This works in REPL/Jupyter/Quarto/Express because the display hook fires on the bare expression statement. It does *not* work in a plain Python script body (the display hook is `print`, not capture). Express has its own runtime to paper over this.

### What we are switching to

The class itself owns a context stack via `contextvars`. The full mechanism:

```python
# Module-level stack, shared across components
_stack: ContextVar[tuple[AllowsChildren, ...]] = ContextVar("_stack", default=())

def push(parent: AllowsChildren) -> Token:
    return _stack.set(_stack.get() + (parent,))

def pop(token: Token) -> None:
    _stack.reset(token)

def active_parent() -> AllowsChildren | None:
    stack = _stack.get()
    return stack[-1] if stack else None

# AllowsChildren mixin
class AllowsChildren:
    children: list[TagChild]

    def __enter__(self) -> Self:
        self._ctx_token = push(self)        # this component is now the active parent
        return self

    def __exit__(self, *exc) -> None:
        pop(self._ctx_token)
        if exc[0] is None:
            dispatch_to_active_parent(self) # add self to whatever is now on top

# UiComponent.__init__ (every component, capturing or not)
class UiComponent:
    def __init_subclass__(cls, **kw):
        # wrap __init__ so the last thing it does is:
        #   parent = active_parent()
        #   if parent is not None: parent.append(self)
        ...
```

`__init__` checks `active_parent()` and appends `self` if a parent is active. This is **construction-time capture**, not display-time capture: nothing depends on `sys.displayhook` or `__repr_html__`.

### Consequence: things must be wrapped

In Express today this works because of the display hook:

```python
with ui.card():
    "Some text"     # routed via __repr_html__-ish path
    42              # also routed
```

Under the stack approach there is no hook on bare values — they are not `AllowsChildren`-aware. The migration: wrap them.

```python
with ui.card():
    ui.markdown("Some text")
    ui.markdown(42)
```

This is the breaking change. The error is mechanical and easy to surface: at the end of `__exit__`, if a parent has any non-`TagChild`-coercible siblings that fell off the floor, emit a clear "this value was discarded; wrap it in `ui.markdown(...)` to render" message. (Detection mechanism TBD — likely a per-block tracer, not a free-form heuristic.)

### Assignment vs. display

A subtle property of the stack approach: **construction inside a `with` block always captures**, even when assigned.

```python
with ui.card() as main:
    slider = ui.input_slider("n", "N", 1, 100, 10)
    # `slider` is bound in the enclosing scope AND has been added to main.children
```

The variable binding is *additional* to the capture, not a substitute for it. To opt out, the author either constructs outside the `with` and uses an explicit `.display()` / `.ui_here()` method at the placement site, or uses `ui.hold(...)` — the `StackCapture` equivalent of `ui.hold()` is a `with`-block that pushes a sentinel onto the stack, so any components constructed inside its body see "no real parent" and are not captured.

```python
slider = ui.input_slider("n", "N", 1, 100, 10)   # top-level: not captured anywhere
with ui.card() as main:
    slider.display()                              # explicit placement
```

The method name (`display` / `show` / `ui_here`) is an open question; `display` is the front-runner.

## `HtmlToolsStack` — push the stack down into `htmltools`

Once `StackCapture` is in `shiny.ui`, the natural next move is to give `htmltools.tags.div(...)` the same context-manager behaviour, using the same shared stack. The change is a small mixin on `Tag`:

```python
class Tag:
    # ... existing fields (name, attrs, children) ...

    def __enter__(self) -> Tag:
        self._ctx_token = push(self)
        return self

    def __exit__(self, *exc) -> None:
        pop(self._ctx_token)
        if exc[0] is None:
            dispatch_to_active_parent(self)
```

This means:

```python
from htmltools import tags

with tags.div(class_="row"):
    tags.span("hello")        # captured by the div
    tags.span("world")
```

Why do this:

- **Symmetry.** Authors writing low-level HTML should not need to know which library happens to own the capture mechanism.
- **Composition.** A Shiny `card` (which subclasses `UiLayout`+`AllowsChildren`) and a `tags.div(...)` participate in the same stack, so they nest with no special-casing.
- **Cleanness.** Strips Shiny-specific behaviour out of Shiny and into the right layer.

The constraint: `htmltools` does not know about Shiny's session. The stack lives in a `contextvars.ContextVar[list[AllowsChildren-like]]`, which is dependency-free and works fine without Shiny. Shiny adds its own layer on top for session-scoped concerns.

### Escape hatch: `tagify()` suppresses capture

`tagify()` is the *intentional* way out of the capture stack. Consider a component whose `tagify()` returns `tags.div(tags.span(42))`:

```python
class my_component(UiLayout):
    def tagify(self) -> Tag:
        return tags.div(tags.span(42))   # constructs inner tags eagerly
```

If `tagify()` runs while some outer `with ui.card():` is still active, those nested `tags.div` and `tags.span` constructions would naively get captured by the surrounding card — even though they are part of *this component's own rendering*, not new children of the user's `with` block.

The rule: **`tagify()` is a capture-suppressing boundary.** Entering `tagify()` pushes a sentinel onto the stack; exiting pops it. Components built inside the body of `tagify()` see "no real parent" and are not appended anywhere implicitly.

```python
def tagify(self) -> Tag:
    with _no_capture():                  # internal helper
        return tags.div(tags.span(42))
```

Two consequences for app authors:

1. Implementers can compose `htmltools` freely inside `tagify()` without polluting the active stack frame.
2. The same rule is reachable from user code: calling `.tagify()` explicitly inside a `with` block produces a `Tag` that is *not* captured. This is the documented way to construct a sub-tree for later placement.

The public API needs naming: a user-facing `with no_capture(): ...` context manager that lets app authors opt out without going through `tagify()`, and a documented "`tagify()` is always a capture-suppressing boundary" rule. Both should land with `HtmlToolsStack`.

## `UnifiedMode` — collapsing Core and Express into one mode

### The mental model

After `ClassComponents` + `StackCapture` + `HtmlToolsStack`, the two-runtime distinction collapses:

- **Core today** = a UI value passed to `App(ui, server)`. No display semantics in the UI definition.
- **Express today** = a script that uses display hooks to capture top-level expressions and an `auto-page` step to wrap them.

After `StackCapture`, **construction-time capture** replaces the display hook. There is no more "Express runtime" in the dispatch sense — only one runtime that supports `with` blocks for composition.

What remains is a presentational choice:

- "I want a `def server(input, output, session): ...` function" → write one. Same as Core today.
- "I want render decorators inline with the UI" → put them inline. The render is session-lazy and binds when a session resolves it.

### Session-lazy reactives

The blocker today: `@render.code def summary(): ...` greedy-grabs the current session. Inside an Express script that's fine; in Core mode there is no session yet at UI-construction time.

Proposal: every `@render.*` and `@reactive.calc` defined at UI-construction time records itself against a *session-resolver*. The first time the value is *requested*, it binds:

- If we are inside a session (because Shiny is serving a connection), bind to that session.
- If we are not, bind to the **root session** (the default scope).
- If we are inside a `with global_session():` block, force binding to the root/global session regardless.

This delays the session requirement from "decorator-evaluation time" to "first-read time." It does not require running the app file twice.

```python
@reactive.calc          # session-lazy
def first_content():
    return "42"

with ui.card() as main:
    @reactive.calc      # session-lazy; resolves to the per-session instance on read
    def extra_content():
        return f"Extra: {first_content()}"

    @render.code        # binds to whatever session asks for it
    def summary():
        return extra_content()

# global-scoped explicitly
with global_session():
    @reactive.calc
    def shared_counter():
        return 0
```

### Modules

`@module` keeps the Express-shaped signature in `UnifiedMode`. A module declared inside a `with` block is captured as a child of the active parent, and its body runs with its own scoped `input` / `output` / `session`:

```python
with ui.card() as main:
    @module
    def my_panel(input, output, session):
        ui.markdown("nested UI")
        ui.input_action_button("go", "Go")

        @render.code
        def out():
            return f"clicked {input.go()} times"
```

This matches what app authors already write in Express today. The names `input`, `output`, `session` are importable from `shiny` at module scope (`from shiny import input, output, session`) for the top-level UI body; inside `@module`, the parameters shadow them with module-scoped versions. The decorator continues to handle id namespacing and per-session resolution as it does today.

### What's actually different from "Express today"

- No display hook (`StackCapture`).
- `with` blocks compose UI in *both* styles (`StackCapture`).
- `App(...)` accepts a UI value, with or without a server function.
- `with global_session():` is the explicit opt-out from session scoping.
- `auto-page` heuristics are replaced with explicit page wrappers — authors say `App(page_sidebar(...))` rather than relying on inference.

## `InstanceAccessors` — `.value()` / `.update()` on instances (NOT in this proposal)

Sketched fully in [`decisions/2026-05-19-class-based-ui-type-system.md`](./2026-05-19-class-based-ui-type-system.md) and examples 14–15. The structural change here doesn't require it. Open questions:

- Reading: `slider.value()` (reactive calc method, explicit) vs `slider.value` (property, implicit reactivity) vs Marimo-style `slider.value = 42` setter (Joe-style concern: hides reactivity).
- Multiple values per component: namespace them (`plot.value.click()`, `plot.value.brush()`) so they auto-complete together — or prefix individually (`plot.value_click()`, `plot.value_brush()`).
- Update method placement: `Updatable` as a separate mixin vs. always-present on `UiInput`.

These should be decided in a follow-up after `UnifiedMode` is in place and we have real per-session ergonomics to compare against.

## Implementation notes

### Where the prototypes live today

| Package | Purpose | Notes |
|---|---|---|
| `pkg-py/src/shinyuiclassonly/` | `ClassComponents` reference: class hierarchy + `AllowsChildren` + `_ctx_stack` | Stand-in for what gets ported to `posit-dev/py-shiny` for `ClassComponents` + `StackCapture` + `HtmlToolsStack` |
| `pkg-py/src/shinyui/` | `InstanceAccessors` reference: above + session-bound `.value()` / `.update()` / per-session id registry | Demonstrates the fuller vision; not required by this proposal |
| `examples/app-py/14-unified-ui-prototype/` | `shinyui` in Core form | |
| `examples/app-py/15-shinyui-with-blocks/` | `shinyui` in Express `with`-block form | |
| `examples/app-py/16-shinyuiclassonly-core/` | `shinyuiclassonly` in Core form (this proposal's structural step) | |
| `examples/app-py/17-shinyuiclassonly-express/` | `shinyuiclassonly` in Express `with`-block form | |

### Files that change in `py-shiny`

Roughly:

- `shiny/ui/_*.py` — every component factory becomes a class (`UiInput`, `UiOutput`, or `UiLayout`+`AllowsChildren` subclass). `tagify()` keeps the old factory body verbatim.
- `shiny/_utils/_ctx_stack.py` (new) — the push/pop primitive used by `AllowsChildren` and by `htmltools` after `HtmlToolsStack`.
- `shiny/express/` — `_recall.py` and display-hook plumbing collapse into a thin compatibility shim, eventually deletable.
- `shiny/render/` and `shiny/reactive/` — `@render.*` and `@reactive.calc` gain a session-lazy resolution mode (`UnifiedMode`).
- `htmltools/_core.py` — `Tag.__enter__` / `Tag.__exit__` adopt the same `contextvars` stack (`HtmlToolsStack`).

### Notebook display-hook story

A class on the stack at depth 0 (no parent active) and reached by `sys.displayhook` should still produce a `_repr_html_`. The proposed rule:

- If `tagify()`-able and stack depth is 0 → produce `_repr_html_` (notebook renders it).
- If stack depth > 0 → no-op `_repr_html_` (already captured by parent).

This needs a spike to confirm Jupyter, Quarto-Python, and VS Code interactive all behave correctly.

### `dev` branch strategy

- Branch: `dev` on `posit-dev/py-shiny` (no `v2` suffix — we may converge on a non-v2 path; the name doesn't need to commit).
- Planning artifacts (this doc, follow-up specs) live in the branch under `docs/` or `decisions/` and are deleted before merge.
- Releases continue from `main` for Shiny 1.x. `dev` is parallel and does not block 1.x.
- PRs into `dev` are how iteration happens; review checkpoints every two weeks.

### Non-goals for this proposal

- React rendering / `shinyreact` integration. The "decouple intent from rendering" framing is the long-term enabling argument, but `shinyreact` continues with its current `ui.tsx` and JSON-spec approach independent of this work. The two converge later, on their own timelines.
- `.value()` / `.update()` ergonomics (`InstanceAccessors`). Tracked separately.
- R-package equivalent. Out of scope; revisit once the Python design stabilises.

---

## Appendix — meeting context

This proposal crystallises the 2026-05-20 meeting with Barret, Carson, Liz, and Garrick. Key resolutions captured:

- Use stack-based capture, not display hooks, as the canonical mechanism (Carson + Liz agreed).
- "Things must be wrapped" — accepted as the price of stack capture (all four).
- `auto-page` is replaced by explicit `App(page_*(...))` (Garrick raised; agreed).
- `InstanceAccessors` is deferred (`slider.value()` vs `slider.value` is unresolved).
- Doc target: Friday 2026-05-29 for team review; Joe / Winston / Andrew sign-off in Boston.
