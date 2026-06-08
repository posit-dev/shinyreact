# Stack-based child capture (and unified Core/Express mode)

**Date:** 2026-05-20
**Status:** Proposal — **contested.** For review by the Shiny team Friday 2026-05-29, then Joe / Winston / Andrew sign-off
**Scope:** `py-shiny` (not `shinyreact`)
**Depends on:** [`decisions/2026-05-20-class-based-ui-components.md`](./2026-05-20-class-based-ui-components.md) — the class hierarchy. This proposal builds on it.
**Branch plan:** prototype in a `dev` branch on `posit-dev/py-shiny`; targets a **Shiny v2 / breaking** release
**Related:**
- `examples/app-py/16-shinyuiclassonly-core/` and `17-shinyuiclassonly-express/` — prototypes whose `AllowsChildren` already carries the context stack.

> **Two documents, two ideas.** Early feedback was that the **class hierarchy is acceptable** but **replacing the capture mechanism with a stack is not** — at least not yet. This doc isolates the contested half so it can be debated, deferred, or rejected without holding up [class-based UI components](./2026-05-20-class-based-ui-components.md). Read that doc first; everything here assumes components are already classes.

---

## TL;DR — for decision makers

This proposal changes *how* a UI component's children are collected when you write a `with` block, and what that unlocks. Three stages:

1. **`StackCapture`** — replace Express's "print to capture" trick with an explicit stack. Express today uses Python's display hook (`sys.displayhook`) to detect that a UI element was created at the top of a `with` block and stitch it into the parent. We replace that with an explicit push/pop context stack maintained by the class. A component captures children when it is *constructed* inside a `with` block, not when it is printed.
2. **`HtmlToolsStack`** — push the stack primitive down into `htmltools` once `StackCapture` is in. Plain `htmltools.tags.div(...)` participates in the same stack, so the mechanism is shared between Shiny and any other consumer of `htmltools`.
3. **`UnifiedMode`** — collapse "Core mode" and "Express mode" into one mode. Once child capture is explicit, the two runtimes converge: the same app file works whether or not a `server` function is present, with `with global_session():` as the opt-in for declarations that should *not* be session-scoped.

### Why this is contested

`StackCapture` is a **breaking change to Express**. Today a bare literal at the top of a `with` block (`"text"`, `42`) renders because the display hook catches it. Under construction-time capture there is no hook on bare values, so they silently fall through unless wrapped (`ui.markdown("text")`). That is a pervasive, if mechanical, migration — and it commits us to a Shiny v2.

The upside is real (context managers in Core, one mental model, a path to alternative renderers), but the cost is high enough that the team's current read is "classes yes, stack not yet."

### What it buys

- **Context managers in Core.** Authors get the nested-`with` composition style without Express's display-hook semantics — in plain scripts, notebooks, anywhere.
- **One mental model.** The Core/Express split (server function vs display hook) collapses to a single runtime; "Express" becomes a writing style, not a separate dispatch path.
- **A cleaner primitive.** Capture stops depending on `sys.displayhook` — which Shiny shares with Jupyter/IPython and has to fight with.

### What it costs

- **Shiny v2 / breaking.** Every top-level value in a `with` block must be a recognised component. Bare literals no longer render. Migration is mechanical but pervasive.
- **Documentation overhaul.** The website, tutorials, and examples need a re-pass to reflect the unified mental model.
- **Notebook-render behaviour to validate.** Display hooks are used by Jupyter/IPython for rich output. The stack approach needs an explicit story for "I'm in a notebook, top-level objects should still render."

### Recommended path

- Treat this as a **separate decision from classes.** It can be deferred indefinitely without blocking [class-based UI components](./2026-05-20-class-based-ui-components.md).
- If pursued: land `StackCapture` and `HtmlToolsStack` together, then `UnifiedMode` as a follow-up.
- If deferred: the class hierarchy continues to use today's display-hook capture; revisit when there is appetite for a breaking release.

---

## What we are asking decision makers to approve (or reject)

1. Whether to **replace display-hook capture with construction-time stack capture** at all.
2. If yes, the **breaking-change commitment**: Express requires all rendered top-level values to be wrapped components, post-v2.
3. If yes, the staging: **`StackCapture` + `HtmlToolsStack` together, then `UnifiedMode`**.

A "no" answer keeps today's Express capture and is fully compatible with shipping class-based UI. A "not yet" answer parks this doc until a v2 is on the table.

---

## What changes for an app author

### Express today (Shiny 1.x)

```python
from shiny.express import ui, render, input

with ui.card(id="main"):
    "Title"                                  # renders — caught by display hook
    ui.input_slider("n", "N", 1, 100, 10)

    @render.plot
    def plot(): ...
```

The top-level `"Title"` and `ui.input_slider(...)` render because Python's display hook is hijacked.

### Under this proposal (Shiny v2)

```python
from shiny import App, ui, render

with ui.card(id="main") as main:
    ui.markdown("Title")                     # MUST wrap — no display hook to catch a bare str
    ui.input_slider("n", "N", 1, 100, 10)
    ui.output_plot("plot")

def server(input, output, session): ...        # optional, see UnifiedMode

app = App(main, server)
```

Or, when `UnifiedMode` lands:

```python
from shiny import ui, render

with ui.card(id="main") as main:
    ui.markdown("Title")
    ui.input_slider("n", "N", 1, 100, 10)

    @render.plot
    def plot(): ...

app = App(main)   # session-lazy under the hood; no server function needed
```

### Migration in one sentence

Wrap top-level bare values in a component (`ui.markdown("text")`, etc.); everything else stays the same.

---

## Open questions called out for the team

- **Notebook display hook.** Shiny shares the `sys.displayhook` mechanism with Jupyter. The stack approach must not break notebook rendering; one possibility is "print only when stack depth is zero." **Needs prototype validation.**
- **`auto_page` in Express.** Today Express's "auto-page" wrapping inspects what was displayed at the top level to decide between `page_fluid` / `page_sidebar` / `page_navbar`. Under the stack model, this becomes explicit (`App(main_layout)`) — confirming this is acceptable to users is part of the v2 messaging.
- **Reactives declared inside a `with` block.** A `@reactive.calc` inside a `with ui.card():` block should still be a function (Joe's "explicit reactivity" principle); under the unified mode we want it to be session-lazy so it can be defined once and resolved per session. **Solvable; needs spec.**
- **Detecting the dropped-value error.** When a bare literal falls through, we want a clear "wrap this in `ui.markdown(...)`" message, not silent loss. The detection mechanism (a per-block tracer?) is **TBD**.

---

## Risks

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Migration noise for existing Express apps | High | Medium | Mechanical fix; clear error messages; codemod script if needed. |
| Notebook rendering regressions | Medium | High | Step-zero spike: validate display-hook behaviour against Jupyter, Quarto, VS Code interactive. |
| Documentation debt blocks v2 release | High | Medium | Liz involved from day one; doc rewrite tracked as a parallel workstream. |
| Authors confused by "where does this render?" | Medium | Medium | Stack rule is simple: "constructed inside a `with` → goes into that parent; else → top level." Document with a flowchart. |
| Team appetite for a breaking v2 is low | Medium | High | This doc is deferrable; classes ship regardless. |

---

## Timeline

- **2026-05-29 (Fri):** team review of this doc (alongside the class-based doc).
- **By 2026-06-02:** Joe / Winston / Andrew gut-check in Boston (in person, ~1–2 hours).
- **Shiny v2 release:** date deliberately not committed here; depends on doc rewrite, v2 messaging plan, and whether this proposal is accepted at all.

---
---

# Technical details

This section is the implementation reference. Decision makers do not need to read past this line.

Everything below assumes the [class hierarchy](./2026-05-20-class-based-ui-components.md) (`UiComponent`, `AllowsChildren`, etc.) is already in place.

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

# AllowsChildren mixin (from the class-hierarchy doc) gains push/pop
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
- **Composition.** A Shiny `card` (a `UiLayout`, which carries `AllowsChildren`) and a `tags.div(...)` participate in the same stack, so they nest with no special-casing.
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

After `StackCapture` + `HtmlToolsStack`, the two-runtime distinction collapses:

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

`@module` in `UnifiedMode` takes **no required parameters** — same shape as `@reactive.calc` and `@reactive.effect`. A module initialized inside a `with` block is captured as a child of the active parent, and its body composes nested UI directly:

```python
with ui.card() as main:
    @module
    def my_panel():
        ui.markdown("nested UI")
        go = ui.input_action_button("go", "Go")

        @render.code
        def out():
            return f"clicked {go.value()} times"
```

Why the empty signature is enough:

- **Inputs** come from the input-class instances themselves (`go.value()`), not from a passed-in `input` object. This relies on the `InstanceAccessors` stage from the [class-based doc](./2026-05-20-class-based-ui-components.md); until that lands, authors can read inputs via `input.<id>()` imported at module scope.
- **`output`** is no longer a parameter app authors interact with. Render decorators register themselves directly; if a render needs the legacy registry, it can reach it via the active session.
- **`session`** is rarely needed once `.update()` / `.value()` live on instances. When something genuinely needs it (custom messages, lifecycle hooks), call `shiny.session.require_active_session()` from inside the module body.

Parameters can still be **optional**, mirroring the way server functions today let you drop unused names:

```python
@module
def my_panel(input):                       # only inputs needed
    ...

@module
def my_panel(input, session):              # inputs + session
    ...
```

The decorator inspects the signature and passes only the names the function declares. This matches the shape app authors already write for `@reactive.calc` / `@reactive.effect` and keeps the syntactic space clean. The decorator continues to handle id namespacing and per-session resolution as it does today.

### What's actually different from "Express today"

- No display hook (`StackCapture`).
- `with` blocks compose UI in *both* styles (`StackCapture`).
- `App(...)` accepts a UI value, with or without a server function.
- `with global_session():` is the explicit opt-out from session scoping.
- `auto-page` heuristics are replaced with explicit page wrappers — authors say `App(page_sidebar(...))` rather than relying on inference.

## Implementation notes

### Files that change in `py-shiny`

Roughly:

- `shiny/_utils/_ctx_stack.py` (new) — the push/pop primitive used by `AllowsChildren` and by `htmltools` after `HtmlToolsStack`.
- `shiny/ui/_*.py` — `AllowsChildren.__enter__` / `__exit__` and `UiComponent.__init__` gain the stack hooks (the class lattice itself comes from the [class-based doc](./2026-05-20-class-based-ui-components.md)).
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

- The class hierarchy itself. Tracked in the [class-based doc](./2026-05-20-class-based-ui-components.md); this proposal assumes it and only changes the capture mechanism.
- React rendering / `shinyreact` integration. Independent of this work.
- R-package equivalent. Out of scope; revisit once the Python design stabilises.

---

## Appendix — meeting context

This proposal isolates the stack-capture portion of the 2026-05-20 meeting with Barret, Carson, Liz, and Garrick. Key points captured:

- Stack-based capture vs display hooks was discussed as the canonical mechanism; the appeal is context managers in Core and one mental model.
- "Things must be wrapped" was acknowledged as the price of stack capture, and as a breaking change requiring a v2.
- `auto-page` would be replaced by explicit `App(page_*(...))` (Garrick raised).
- Garrick suggested staging: prove the class hierarchy first; keep the two modes; only later evaluate how far to push toward unification. Subsequent feedback narrowed this further — classes are acceptable, the stack change is not (yet) — which is why this doc is split out as the contested half.
- Doc target: Friday 2026-05-29 for team review; Joe / Winston / Andrew sign-off in Boston.
